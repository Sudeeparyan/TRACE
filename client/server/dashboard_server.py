"""
TRACE Dashboard Backend Server
Provides WebSocket streaming and REST API endpoints for the React dashboard

Integrated with Principal Agent (ADK Framework) for AI-powered auto-remediation.
"""

import sys
import os

# Fix Windows console encoding for emoji support - must be done first
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import time
import random
from datetime import datetime
import json

# Add project paths for shared imports
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.dirname(SERVER_DIR)
ROOT_DIR = os.path.dirname(CLIENT_DIR)
for path in (CLIENT_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.append(path)

from principal_agent_bridge import PrincipalAgentBridge
from agent_integration import agent_integration

# Try to import Bedrock service for AWS mode
try:
    import bedrock_service
    BEDROCK_AVAILABLE = bedrock_service.is_available()
except ImportError:
    BEDROCK_AVAILABLE = False
    bedrock_service = None

# Determine AI backend
AI_BACKEND = os.getenv('TRACE_AI_BACKEND', 'auto')  # 'auto', 'bedrock', 'gemini'

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active connections by region
active_connections = {}

# Bridge to the Principal Agent toolchain
bridge = PrincipalAgentBridge()

# Print integration status at startup
print("\n" + "=" * 60)
print("TRACE Dashboard Server - Integration Status")
print("=" * 60)
integration_status = agent_integration.get_status()
print(
    f"  Principal Agent: {'✅ Available' if integration_status['principal_agent_available'] else '❌ Not Available'}"
)
print(
    f"  ADK Framework:   {'✅ Available' if integration_status['adk_available'] else '❌ Not Available'}"
)
print(
    f"  Gemini AI:       {'✅ Available' if integration_status.get('gemini_available') else '❌ Not Available'}"
)
print(
    f"  AWS Bedrock:     {'✅ Available' if BEDROCK_AVAILABLE else '❌ Not Available'}"
)
print(
    f"  AI Backend:      {AI_BACKEND.upper()} {'(using Bedrock)' if BEDROCK_AVAILABLE and AI_BACKEND in ['auto', 'bedrock'] else '(using Gemini)' if integration_status.get('gemini_available') else '(fallback)'}"
)
print(f"  Mode:            {integration_status['mode'].upper()}")
print("=" * 60 + "\n")


# REST API Endpoints
@app.route("/api/health/<region>", methods=["GET"])
def get_health(region):
    """Get system health for a region"""
    return jsonify(bridge.get_system_health(region))


@app.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    """Get historical telemetry data"""
    region = request.args.get("region", "us-east-1")
    count = int(request.args.get("count", 100))
    data = bridge.get_telemetry_series(region, count)
    return jsonify(data)


@app.route("/api/active-users/<region>", methods=["GET"])
def get_active_users(region):
    """Get active users for a region"""
    history = bridge.get_active_users_history(region, 1)
    return jsonify(history[-1] if history else bridge.next_active_users_point(region))


@app.route("/api/issues", methods=["GET"])
def get_issues():
    """Get active issues (only non-resolved issues)"""
    region = request.args.get("region", "us-east-1")
    return jsonify(bridge.get_issues(region))


@app.route("/api/issues/seed", methods=["POST"])
def seed_issues():
    """Seed initial issues for testing or startup"""
    data = request.json or {}
    region = data.get("region", "us-east-1")
    count = data.get("count", 2)
    return jsonify(bridge.seed_initial_issues(region, count))


@app.route("/api/issues/create", methods=["POST"])
def force_create_issue():
    """
    Force create a new issue immediately (for demo purposes).
    This bypasses probability checks and creates an issue right away.

    Request body:
    - region: The region for the issue (default: us-east-1)
    - severity: critical, high, or medium (optional)
    - issue_type: partial match for issue type name (optional)

    The created issue will be emitted via WebSocket to all connected clients.
    """
    data = request.json or {}
    region = data.get("region", "us-east-1")
    severity = data.get("severity")
    issue_type = data.get("issue_type")

    issue = bridge.force_create_issue(region, severity, issue_type)

    if issue:
        # Emit to all connected clients immediately
        socketio.emit("issue", issue, room=region)
        return jsonify({"success": True, "issue": issue})
    else:
        return jsonify({"success": False, "error": "Could not create issue"}), 500


@app.route("/api/demo/mode", methods=["POST"])
def set_demo_mode():
    """
    Configure demo mode settings.

    Request body:
    - enabled: true/false to enable/disable demo mode
    - auto_heal: true/false to enable/disable auto-healing
    - interval: seconds between auto-generated issues
    """
    data = request.json or {}
    enabled = data.get("enabled", True)
    auto_heal = data.get("auto_heal", True)
    interval = data.get("interval", 10)

    result = bridge.set_demo_mode(enabled, auto_heal, interval)
    return jsonify({"success": True, **result})


@app.route("/api/demo/status", methods=["GET"])
def get_demo_status():
    """Get current demo mode status."""
    return jsonify(bridge.get_demo_status())


@app.route("/api/remediation/trigger", methods=["POST"])
def trigger_remediation():
    """
    Trigger a remediation action using the Principal Agent.

    This endpoint connects to the AI-powered Principal Agent for intelligent
    auto-remediation when available, falling back to direct tool execution otherwise.
    """
    data = request.json
    issue_id = data.get("issueId")
    action = data.get("action")

    # Get the full issue data for the agent
    region = data.get("region", "us-east-1")
    issues = bridge.get_issues(region)
    issue = next((i for i in issues if i.get("id") == issue_id), None)

    if not issue:
        # Create a minimal issue object for remediation
        issue = {
            "id": issue_id,
            "title": f"Issue {issue_id}",
            "severity": "medium",
            "suggestedAction": action or "restart_agent",
            "affectedTowers": ["Tower-1"],
            "activeAgent": "monitoring_agent",
        }

    # Use the agent integration for AI-powered remediation
    agent_result = agent_integration.auto_remediate(issue, action)

    # Also update the bridge for state management
    bridge_result, resolution = bridge.trigger_remediation(issue_id, action)

    # Merge results - prefer agent response
    resolution["agent_response"] = agent_result.get("agent_response")
    resolution["source"] = agent_result.get("source", "fallback")
    resolution["issueId"] = issue_id  # Include issueId for frontend removal

    # Emit resolution event to connected clients
    socketio.emit("resolution", resolution)

    payload = {
        "success": agent_result.get("success", False),
        "issueId": issue_id,
        "action": agent_result.get("operation", action),
        "timestamp": agent_result.get("timestamp", datetime.utcnow().isoformat()),
        "message": agent_result.get("message", "Remediation executed"),
        "agent_response": agent_result.get("agent_response"),
        "source": agent_result.get("source", "unknown"),
    }
    return jsonify(payload)


@app.route("/api/issue/analyze", methods=["POST"])
def analyze_issue():
    """
    Analyze an issue using the Principal Agent AI.

    This endpoint sends the issue to the principal agent for detailed
    analysis and recommendations.
    """
    data = request.json
    issue_id = data.get("issueId")
    region = data.get("region", "us-east-1")

    # Get the full issue data
    issues = bridge.get_issues(region)
    issue = next((i for i in issues if i.get("id") == issue_id), data.get("issue", {}))

    if not issue:
        return jsonify({"success": False, "error": "Issue not found"}), 404

    # Get AI analysis
    analysis = agent_integration.analyze_issue(issue)

    return jsonify(
        {
            "success": True,
            "issueId": issue_id,
            "analysis": analysis.get("analysis"),
            "source": analysis.get("source"),
            "timestamp": analysis.get("timestamp"),
        }
    )


@app.route("/api/integration/status", methods=["GET"])
def get_integration_status():
    """Get the Principal Agent integration status."""
    return jsonify(agent_integration.get_status())


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint for interacting with the Principal Agent.

    This endpoint allows users to send messages and receive AI-powered responses
    from the Principal Agent.
    """
    data = request.json
    message = data.get("message", "")
    context = data.get("context", "trace_dashboard")

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    # Get response from the agent
    result = agent_integration.chat(message, context)

    return jsonify(result)


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """
    Streaming chat endpoint for real-time AI responses.

    Uses Server-Sent Events (SSE) for streaming the response.
    """
    from flask import Response, stream_with_context

    data = request.json
    message = data.get("message", "")
    context = data.get("context", "trace_dashboard")

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    # Try to use Gemini streaming
    try:
        from gemini_service import gemini_service, GEMINI_AVAILABLE

        if GEMINI_AVAILABLE and gemini_service:

            def generate():
                yield 'data: {"type": "start"}\n\n'

                full_response = ""
                for chunk in gemini_service.chat_stream(message, context):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                yield f"data: {json.dumps({'type': 'end', 'full_response': full_response})}\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
    except ImportError:
        pass

    # Fallback to regular chat
    result = agent_integration.chat(message, context)
    return jsonify(result)


@app.route("/api/telemetry/analyze", methods=["POST"])
def analyze_telemetry():
    """
    Analyze telemetry data using AI.
    """
    data = request.json
    telemetry = data.get("telemetry", {})
    analysis_type = data.get("analysis_type", "comprehensive")

    try:
        from gemini_service import gemini_service, GEMINI_AVAILABLE

        if GEMINI_AVAILABLE and gemini_service:
            result = gemini_service.analyze_telemetry(telemetry, analysis_type)
            return jsonify(result)
    except ImportError:
        pass

    return jsonify(
        {
            "success": False,
            "error": "AI analysis not available",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/api/json/analyze", methods=["POST"])
def analyze_json():
    """
    Analyze uploaded JSON data using AI.
    """
    data = request.json
    json_data = data.get("data", [])
    query = data.get("query", "comprehensive analysis")

    try:
        from gemini_service import gemini_service, GEMINI_AVAILABLE

        if GEMINI_AVAILABLE and gemini_service:
            result = gemini_service.analyze_json_data(json_data, query)
            return jsonify(result)
    except ImportError:
        pass

    return jsonify(
        {
            "success": False,
            "error": "AI analysis not available",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/api/resolutions", methods=["GET"])
def get_resolutions():
    """Get resolution history"""
    region = request.args.get("region", "us-east-1")
    limit = int(request.args.get("limit", 20))
    return jsonify(bridge.get_resolutions(region, limit))


@app.route("/api/agents/status", methods=["GET"])
def get_agent_status():
    """Get status of all agents"""
    return jsonify(bridge.get_agent_statuses())


# WebSocket Event Handlers
@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    emit("connected", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected")


@socketio.on("subscribe")
def handle_subscribe(data):
    """Subscribe client to a region"""
    region = data.get("region", "us-east-1")
    join_room(region)
    print(f"Client subscribed to region: {region}")

    # Start streaming data for this region
    if region not in active_connections:
        active_connections[region] = True

    # Send immediate snapshots so the UI updates without delay
    emit("telemetry", bridge.next_telemetry_point(region))
    emit("activeUsers", bridge.next_active_users_point(region))
    health = bridge.get_system_health(region)
    emit("health", {"score": health["score"], "status": health["status"]})


# Background task to stream data
def stream_data():
    """Stream telemetry data to all connected clients"""
    issue_counter = {}  # Track when to generate issues per region

    while True:
        socketio.sleep(1)

        for region in list(active_connections.keys()):
            # Send telemetry snapshot
            socketio.emit("telemetry", bridge.next_telemetry_point(region), room=region)

            current_second = int(time.time())

            # Send active users (every 2 seconds)
            if current_second % 2 == 0:
                socketio.emit(
                    "activeUsers", bridge.next_active_users_point(region), room=region
                )

            # Send health (every 5 seconds)
            if current_second % 5 == 0:
                health = bridge.get_system_health(region)
                socketio.emit(
                    "health",
                    {"score": health["score"], "status": health["status"]},
                    room=region,
                )

            # Demo mode: more frequent issue generation
            if bridge.demo_mode:
                # Initialize counter for region
                if region not in issue_counter:
                    issue_counter[region] = 0
                issue_counter[region] += 1

                # Generate issue based on demo interval
                if issue_counter[region] >= bridge.demo_issue_interval:
                    issue_counter[region] = 0
                    # Higher probability in demo mode (70%)
                    if random.random() < 0.7:
                        issue = bridge.maybe_new_issue(region)
                        if issue:
                            print(
                                f"🚨 Demo mode: Generated issue '{issue.get('title')}' for {region}"
                            )
                            socketio.emit("issue", issue, room=region)

                # Check for auto-healing
                if bridge.auto_heal_enabled:
                    issue_id_to_heal = bridge.check_auto_heal(region)
                    if issue_id_to_heal:
                        print(f"🔧 Auto-healing issue {issue_id_to_heal} in {region}")
                        # Trigger auto-remediation through the agent integration
                        issues = bridge.get_issues(region)
                        issue = next(
                            (i for i in issues if i.get("id") == issue_id_to_heal), None
                        )

                        if issue:
                            action = issue.get("suggestedAction", "restart_agent")
                            # Use agent integration for AI-powered auto-remediation
                            agent_result = agent_integration.auto_remediate(
                                issue, action
                            )
                            bridge_result, resolution = bridge.trigger_remediation(
                                issue_id_to_heal, action
                            )

                            resolution["agent_response"] = agent_result.get(
                                "agent_response"
                            )
                            resolution["source"] = agent_result.get(
                                "source", "auto_heal"
                            )
                            resolution["issueId"] = issue_id_to_heal
                            resolution["auto_healed"] = True

                            # Emit resolution to all clients
                            socketio.emit("resolution", resolution, room=region)
                            print(
                                f"✅ Auto-healed issue {issue_id_to_heal}: {resolution.get('summary')}"
                            )
            else:
                # Normal mode: Send random issues (every 30 seconds)
                if current_second % 30 == 0:
                    issue = bridge.maybe_new_issue(region)
                    if issue:
                        socketio.emit("issue", issue, room=region)


if __name__ == "__main__":
    # Start background streaming task
    socketio.start_background_task(stream_data)

    # Run the server
    # Note: use_reloader=False prevents infinite restarts from watchdog detecting
    # changes in other venv directories outside the project
    print("Starting TRACE Dashboard Backend on http://localhost:8000")
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)
