"""Utility bridge that maps principal_agent tooling outputs to dashboard-friendly data."""

from __future__ import annotations

import random
import sys
import threading
import time
import json
import os
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional
from uuid import uuid4

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Import Gemini Service for AI-powered analysis
try:
    from gemini_service import gemini_service, GEMINI_AVAILABLE
except ImportError:
    GEMINI_AVAILABLE = False
    gemini_service = None

# Load real telemetry data for AI analysis
REAL_TELEMETRY_DATA = None
try:
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "trace_reduced_20.json",
    )
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            REAL_TELEMETRY_DATA = json.load(f)
        print(
            f"✅ Loaded {len(REAL_TELEMETRY_DATA)} telemetry records from trace_reduced_20.json"
        )
except Exception as e:
    print(f"⚠️ Could not load telemetry data: {e}")

# Try to import principal_agent tools, but provide fallbacks if not available
try:
    from principal_agent.tools.health_monitor import (
        check_system_health,
        get_agent_status as pa_get_agent_status,
    )
    from principal_agent.tools.dashboard import (
        generate_incident_report,
        get_system_metrics,
    )
    from principal_agent.tools.remediation import (
        redeploy_agent,
        restart_agent,
        reroute_traffic,
    )

    PRINCIPAL_AGENT_AVAILABLE = True
except ImportError:
    PRINCIPAL_AGENT_AVAILABLE = False

    # Fallback functions for standalone mode
    def check_system_health():
        return {"overall_status": "healthy", "components": {}}

    def pa_get_agent_status(agent_name):
        return {
            "status": "active",
            "uptime_seconds": random.randint(1000, 100000),
            "metrics": {},
            "resource_usage": {},
        }

    def generate_incident_report(incident_id):
        return {
            "incident_id": incident_id,
            "root_cause": random.choice(
                [
                    "High_Traffic_Load",
                    "Network_Congestion",
                    "Energy_Spike",
                    "TRX_Overload",
                ]
            ),
            "status": "Active",
            "affected_components": [f"Tower-{random.randint(1, 10)}"],
            "remediation_actions": [
                {"action": "Scale resources"},
                {"action": "Reroute traffic"},
            ],
        }

    def get_system_metrics(metric_type="all"):
        return {
            "energy_metrics": {
                "current_consumption_kwh": random.uniform(80, 120),
                "peak_consumption_kwh": 150,
            },
            "traffic_metrics": {
                "current_traffic_gbps": random.uniform(30, 90),
                "peak_traffic_gbps": 100,
                "total_connections": random.randint(10000, 40000),
            },
            "health_metrics": {
                "incidents_count": random.randint(0, 3),
            },
        }

    def redeploy_agent(agent_name):
        return {
            "success": True,
            "operation": "redeploy_agent",
            "message": f"Agent {agent_name} redeployed successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def restart_agent(agent_name):
        return {
            "success": True,
            "operation": "restart_agent",
            "message": f"Agent {agent_name} restarted successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reroute_traffic(source, target, percentage):
        return {
            "success": True,
            "operation": "reroute_traffic",
            "message": f"Rerouted {percentage}% traffic from {source} to {target}",
            "timestamp": datetime.utcnow().isoformat(),
        }


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Return value constrained within [minimum, maximum]."""
    return max(minimum, min(maximum, value))


class PrincipalAgentBridge:
    """Adapts principal_agent tool outputs for the dashboard server."""

    STATUS_SCORE_RANGES: Dict[str, List[int]] = {
        "healthy": [93, 98],
        "degraded": [70, 85],
        "critical": [45, 65],
    }

    DEFAULT_REGIONS = ["us-east-1", "us-west-2", "eu-central-1"]

    AGENT_TRACE = [
        "Monitoring",
        "Prediction",
        "Decision xApp",
        "Action",
        "Learning",
    ]

    OPTIMIZATION_ACTIONS = [
        "Load Balancing",
        "TRX Optimization",
        "Energy Saver",
        "None",
    ]

    REMEDIATION_ACTIONS = [
        "restart_agent",
        "redeploy_agent",
        "reroute_traffic",
    ]

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.telemetry_history: Dict[str, Deque[Dict]] = {}
        self.active_user_history: Dict[str, Deque[Dict]] = {}
        self.issue_registry: Dict[str, Dict] = {}
        self.resolution_log: Deque[Dict] = deque(maxlen=200)
        self.agent_names = [
            "principal_agent",
            "regional_coordinator",
            "monitoring_agent",
            "prediction_agent",
            "decision_xapp_agent",
            "action_agent",
            "learning_agent",
        ]
        # Demo mode settings
        self.demo_mode = True  # Enable demo mode by default for easier demos
        self.auto_heal_enabled = True  # Auto-heal issues after delay
        self.auto_heal_delay_seconds = 30  # Time before auto-healing kicks in
        self.demo_issue_interval = 10  # Generate issues every N seconds in demo mode

    # ------------------------------------------------------------------
    # Region helpers
    # ------------------------------------------------------------------
    def _ensure_region_buffers(self, region: str) -> None:
        with self.lock:
            if region not in self.telemetry_history:
                self.telemetry_history[region] = deque(maxlen=600)
            if region not in self.active_user_history:
                self.active_user_history[region] = deque(maxlen=600)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def get_system_health(self, region: str) -> Dict:
        """
        Get system health for a region.
        Uses AI analysis if Gemini is available, otherwise uses tool metrics.
        """
        raw = check_system_health()
        score_range = self.STATUS_SCORE_RANGES.get(
            raw.get("overall_status", "healthy"), [80, 95]
        )
        score = round(random.uniform(*score_range), 2)

        # Try to get AI-enhanced health analysis
        ai_analysis = None
        if GEMINI_AVAILABLE and gemini_service and REAL_TELEMETRY_DATA:
            try:
                # Use cached AI analysis (don't call on every request)
                if (
                    not hasattr(self, "_last_health_analysis")
                    or (time.time() - getattr(self, "_last_health_time", 0)) > 60
                ):  # Cache for 60 seconds
                    sample_data = (
                        REAL_TELEMETRY_DATA[:5]
                        if isinstance(REAL_TELEMETRY_DATA, list)
                        else REAL_TELEMETRY_DATA
                    )
                    analysis_result = gemini_service.analyze_telemetry(
                        {
                            "region": region,
                            "metrics": raw,
                            "telemetry_sample": sample_data,
                        },
                        analysis_type="health",
                    )
                    self._last_health_analysis = analysis_result.get("analysis", "")
                    self._last_health_time = time.time()
                ai_analysis = getattr(self, "_last_health_analysis", None)
            except Exception as e:
                print(f"AI health analysis error: {e}")

        return {
            "region": region,
            "score": score,
            "status": raw.get("overall_status", "healthy").title(),
            "details": raw,
            "ai_analysis": ai_analysis,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Telemetry & active users
    # ------------------------------------------------------------------
    def _build_telemetry_point(self, region: str, seconds_back: int = 0) -> Dict:
        """
        Build a telemetry data point.
        Uses real data from trace_reduced_20.json when available,
        combined with system metrics.
        """
        metrics = get_system_metrics(metric_type="all")
        energy = metrics.get("energy_metrics", {})
        traffic = metrics.get("traffic_metrics", {})
        health = metrics.get("health_metrics", {})

        # Use real telemetry data if available
        if REAL_TELEMETRY_DATA and isinstance(REAL_TELEMETRY_DATA, list):
            # Cycle through real data records
            if not hasattr(self, "_telemetry_index"):
                self._telemetry_index = 0

            real_record = REAL_TELEMETRY_DATA[
                self._telemetry_index % len(REAL_TELEMETRY_DATA)
            ]
            self._telemetry_index += 1

            # Extract metrics from real data - map actual field names from trace_reduced_20.json
            # Energy: use power_voltage_v normalized to percentage (typical range 40-55V)
            power_voltage = real_record.get("power_voltage_v", 48)
            energy_pct = ((power_voltage - 40) / 15) * 100  # Normalize 40-55V to 0-100%
            energy_pct = _clamp(energy_pct, 0, 100)

            # Congestion: use bandwidth_utilization_pct directly (already a percentage)
            congestion_pct = real_record.get(
                "bandwidth_utilization_pct", real_record.get("cpu_util_pct", 50)
            )

            # Anomaly score: derive from packet_loss, latency, and detection_confidence
            packet_loss = real_record.get("packet_loss_pct", 0)
            latency = real_record.get("latency_ms", 20)
            detection_confidence = real_record.get("detection_confidence", 0.5)
            # Calculate anomaly: high packet loss, high latency, or detected errors contribute
            anomaly_score = (
                (packet_loss * 10) + (latency / 5) + (detection_confidence * 30)
            )
            anomaly_score = _clamp(anomaly_score, 5, 100)

            # TRX utilization: use cpu_util_pct as a proxy
            trx_utilization = real_record.get("cpu_util_pct", 50)

            # Power draw: derive from power_voltage and connected users
            connected_users = real_record.get("connected_users", 100)
            capacity_users = real_record.get("capacity_users", 1000)
            load_factor = (
                (connected_users / capacity_users) if capacity_users > 0 else 0.5
            )
            power_draw = (
                60 + (load_factor * 60) + random.uniform(-5, 5)
            )  # 60-120 kW range
        else:
            # Fallback to calculated metrics
            peak_energy = energy.get("peak_consumption_kwh") or 1
            peak_traffic = traffic.get("peak_traffic_gbps") or 1

            energy_pct = _clamp(
                (energy.get("current_consumption_kwh", 0) / peak_energy) * 100,
                0,
                100,
            )
            congestion_pct = _clamp(
                (traffic.get("current_traffic_gbps", 0) / peak_traffic) * 100,
                0,
                100,
            )
            anomaly_base = health.get("incidents_count", 0) * 18
            anomaly_score = _clamp(anomaly_base + random.uniform(5, 30), 0, 100)
            trx_utilization = random.gauss(78, 6)
            power_draw = energy.get("current_consumption_kwh", random.uniform(80, 120))

        timestamp = datetime.utcnow() - timedelta(seconds=seconds_back)
        return {
            "region": region,
            "timestamp": timestamp.isoformat(),
            "energy": round(_clamp(energy_pct, 0, 100), 2),
            "congestion": round(_clamp(congestion_pct, 0, 100), 2),
            "anomaly_score": round(_clamp(anomaly_score, 0, 100), 2),
            "traffic_load": round(
                _clamp(congestion_pct + random.uniform(-5, 8), 0, 100), 2
            ),
            "trx_utilization": round(_clamp(trx_utilization, 30, 100), 2),
            "power_draw": round(
                power_draw if power_draw else random.uniform(80, 120), 2
            ),
        }

    def _build_active_users_point(self, region: str, seconds_back: int = 0) -> Dict:
        metrics = get_system_metrics(metric_type="traffic")
        total_connections = metrics.get("traffic_metrics", {}).get(
            "total_connections", random.randint(10000, 40000)
        )
        active_users = int(total_connections * random.uniform(0.6, 0.95))
        timestamp = datetime.utcnow() - timedelta(seconds=seconds_back)
        return {
            "region": region,
            "timestamp": timestamp.isoformat(),
            "activeUsers": active_users,
            "towerCluster": f"Tower-{random.randint(1, 8)}",
            "lastOptimization": random.choice(self.OPTIMIZATION_ACTIONS),
            "surgeDetected": random.random() > 0.9,
        }

    def get_telemetry_series(self, region: str, count: int = 100) -> List[Dict]:
        self._ensure_region_buffers(region)
        with self.lock:
            history = list(self.telemetry_history[region])
        if len(history) < count:
            missing = count - len(history)
            for idx in range(missing, 0, -1):
                point = self._build_telemetry_point(region, seconds_back=idx)
                self._record_telemetry_point(region, point)
            with self.lock:
                history = list(self.telemetry_history[region])
        return history[-count:]

    def get_active_users_history(self, region: str, count: int = 60) -> List[Dict]:
        self._ensure_region_buffers(region)
        with self.lock:
            history = list(self.active_user_history[region])
        if len(history) < count:
            missing = count - len(history)
            for idx in range(missing, 0, -1):
                point = self._build_active_users_point(region, seconds_back=idx)
                self._record_active_users_point(region, point)
            with self.lock:
                history = list(self.active_user_history[region])
        return history[-count:]

    def next_telemetry_point(self, region: str) -> Dict:
        point = self._build_telemetry_point(region)
        self._record_telemetry_point(region, point)
        return point

    def next_active_users_point(self, region: str) -> Dict:
        point = self._build_active_users_point(region)
        self._record_active_users_point(region, point)
        return point

    def _record_telemetry_point(self, region: str, point: Dict) -> None:
        self._ensure_region_buffers(region)
        with self.lock:
            self.telemetry_history[region].append(point)

    def _record_active_users_point(self, region: str, point: Dict) -> None:
        self._ensure_region_buffers(region)
        with self.lock:
            self.active_user_history[region].append(point)

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------
    def get_issues(self, region: str) -> List[Dict]:
        """Get active issues for a region. Does NOT auto-generate new issues."""
        self._cleanup_expired_issues()
        active = [
            issue
            for issue in self._current_issues().values()
            if issue.get("region") == region and issue.get("status") != "Resolved"
        ]
        return [self._serialize_issue(issue) for issue in active]

    def seed_initial_issues(self, region: str, count: int = 2) -> List[Dict]:
        """Seed initial issues for a region (called once on startup or when needed)."""
        self._cleanup_expired_issues()
        active = [
            issue
            for issue in self._current_issues().values()
            if issue.get("region") == region and issue.get("status") != "Resolved"
        ]
        # Only create new issues if we have less than target
        while len(active) < count:
            issue = self._create_issue(region)
            if issue:  # _create_issue may return None if duplicate
                active.append(issue)
        return [self._serialize_issue(issue) for issue in active]

    def force_create_issue(
        self, region: str, severity: str = None, issue_type: str = None
    ) -> Optional[Dict]:
        """
        Force create a new issue immediately (for demo purposes).
        Bypasses probability checks and creates an issue right away.
        """
        self._cleanup_expired_issues()

        # Find available issue type
        with self.lock:
            existing_titles = {
                i.get("title")
                for i in self.issue_registry.values()
                if i.get("status") != "Resolved"
            }

        # If specific issue type requested, check if available
        available_types = [
            t for t in self.ISSUE_TYPES if t["title"] not in existing_titles
        ]

        if issue_type:
            selected_type = next(
                (
                    t
                    for t in available_types
                    if issue_type.lower() in t["title"].lower()
                ),
                None,
            )
            if not selected_type and available_types:
                selected_type = available_types[0]
        elif available_types:
            selected_type = random.choice(available_types)
        else:
            # Reset one resolved issue to create room
            with self.lock:
                resolved_issues = [
                    k
                    for k, v in self.issue_registry.items()
                    if v.get("status") == "Resolved"
                ]
                if resolved_issues:
                    del self.issue_registry[resolved_issues[0]]
            selected_type = random.choice(self.ISSUE_TYPES)

        # Create the issue
        incident_id = f"issue-{uuid4().hex[:8]}"
        incident = generate_incident_report(incident_id.upper())
        severity = severity or random.choice(["critical", "high", "medium"])
        suggested_action = selected_type.get("action", self._suggest_action(severity))

        # Generate affected towers
        num_towers = random.randint(1, 3)
        affected_towers = [f"Tower-{random.randint(1, 12)}" for _ in range(num_towers)]

        issue = {
            "id": incident_id,
            "region": region,
            "title": selected_type["title"],
            "severity": severity,
            "description": selected_type["description"],
            "impactScore": f"{random.randint(60, 99)}%",
            "affectedTowers": affected_towers,
            "status": "Active",
            "agentTrace": self.AGENT_TRACE,
            "activeAgent": random.choice(
                self.AGENT_TRACE[:3]
            ),  # Start with early agents
            "suggestedAction": suggested_action,
            "detailedAnalysis": self._build_issue_analysis(incident),
            "remediationSteps": [
                "Identify root cause from telemetry data",
                "Execute automated remediation",
                "Verify system stability",
                "Update learning model",
            ],
            "agentLogs": self._build_agent_logs(incident),
            "created_at": time.time(),
        }

        with self.lock:
            self.issue_registry[incident_id] = issue

        return self._serialize_issue(issue)

    def set_demo_mode(
        self, enabled: bool, auto_heal: bool = True, interval: int = 10
    ) -> Dict:
        """Configure demo mode settings."""
        self.demo_mode = enabled
        self.auto_heal_enabled = auto_heal
        self.demo_issue_interval = interval
        return {
            "demo_mode": self.demo_mode,
            "auto_heal_enabled": self.auto_heal_enabled,
            "demo_issue_interval": self.demo_issue_interval,
            "auto_heal_delay_seconds": self.auto_heal_delay_seconds,
        }

    def get_demo_status(self) -> Dict:
        """Get current demo mode status."""
        return {
            "demo_mode": self.demo_mode,
            "auto_heal_enabled": self.auto_heal_enabled,
            "demo_issue_interval": self.demo_issue_interval,
            "auto_heal_delay_seconds": self.auto_heal_delay_seconds,
            "active_issues_count": len(
                [
                    i
                    for i in self._current_issues().values()
                    if i.get("status") != "Resolved"
                ]
            ),
        }

    def check_auto_heal(self, region: str) -> Optional[Dict]:
        """
        Check if any issues should be auto-healed and perform healing.
        Returns the resolved issue if auto-healing occurred.
        """
        if not self.auto_heal_enabled:
            return None

        now = time.time()
        with self.lock:
            for issue_id, issue in list(self.issue_registry.items()):
                if issue.get("status") == "Resolved":
                    continue
                if issue.get("region") != region:
                    continue

                created_at = issue.get("created_at", now)
                age = now - created_at

                # Auto-heal after delay
                if age >= self.auto_heal_delay_seconds:
                    # Mark for healing (don't modify while iterating)
                    return issue_id

        return None

    def maybe_new_issue(self, region: str) -> Optional[Dict]:
        """Maybe create a new issue (with probability check and deduplication)."""
        self._cleanup_expired_issues()
        # Lower probability and check we don't have too many active issues
        active_count = len(
            [
                i
                for i in self._current_issues().values()
                if i.get("region") == region and i.get("status") != "Resolved"
            ]
        )
        max_issues = 5 if self.demo_mode else 3
        if active_count >= max_issues:
            return None  # Don't create more if we already have max active

        # Higher probability in demo mode
        probability = 0.6 if self.demo_mode else 0.3
        if random.random() < probability:
            issue = self._create_issue(region)
            if issue:  # _create_issue may return None if duplicate
                return self._serialize_issue(issue)
        return None

    def _current_issues(self) -> Dict[str, Dict]:
        with self.lock:
            return dict(self.issue_registry)

    # Diverse issue types to prevent repetition
    ISSUE_TYPES = [
        {
            "title": "High Traffic Load",
            "description": "Network traffic exceeds optimal levels",
            "action": "reroute_traffic",
        },
        {
            "title": "Network Congestion",
            "description": "Multiple towers reporting bandwidth saturation",
            "action": "reroute_traffic",
        },
        {
            "title": "Energy Spike Detected",
            "description": "Power consumption above threshold",
            "action": "restart_agent",
        },
        {
            "title": "TRX Overload",
            "description": "Transceiver capacity exceeded",
            "action": "reroute_traffic",
        },
        {
            "title": "Agent Process Crash",
            "description": "Agent process crash",
            "action": "redeploy_agent",
        },
        {
            "title": "Memory Leak Detected",
            "description": "Gradual memory increase detected",
            "action": "restart_agent",
        },
        {
            "title": "Latency Spike",
            "description": "Response times exceeding SLA",
            "action": "reroute_traffic",
        },
        {
            "title": "Connection Timeout",
            "description": "Multiple connection timeouts reported",
            "action": "restart_agent",
        },
        {
            "title": "Signal Interference",
            "description": "RF interference affecting coverage",
            "action": "reroute_traffic",
        },
        {
            "title": "Capacity Warning",
            "description": "Tower approaching user capacity limit",
            "action": "reroute_traffic",
        },
    ]

    def _create_issue(self, region: str) -> Optional[Dict]:
        """
        Create a new issue with deduplication.
        Uses AI for anomaly detection if Gemini is available.
        Returns None if a similar issue already exists.
        """
        # Get existing issue titles to avoid duplicates
        with self.lock:
            existing_titles = {
                i.get("title")
                for i in self.issue_registry.values()
                if i.get("status") != "Resolved"
            }

        # Find an issue type not currently active
        available_types = [
            t for t in self.ISSUE_TYPES if t["title"] not in existing_titles
        ]
        if not available_types:
            return None  # All issue types already have active instances

        issue_type = random.choice(available_types)
        incident_id = f"issue-{uuid4().hex[:8]}"
        incident = generate_incident_report(incident_id.upper())
        severity = random.choice(["critical", "high", "medium"])
        suggested_action = issue_type.get("action", self._suggest_action(severity))

        # Try to get AI-enhanced issue analysis
        ai_detailed_analysis = None
        if GEMINI_AVAILABLE and gemini_service:
            try:
                # Get recent telemetry for context
                recent_telemetry = None
                if region in self.telemetry_history:
                    with self.lock:
                        history = list(self.telemetry_history[region])
                    if history:
                        recent_telemetry = history[-5:]  # Last 5 readings

                # Use AI to analyze the issue
                issue_context = {
                    "incident": incident,
                    "region": region,
                    "severity": severity,
                    "recent_telemetry": recent_telemetry,
                }

                # Get AI recommendations (with caching built into gemini_service)
                ai_result = gemini_service.get_recommendations(
                    {
                        "id": incident_id,
                        "title": incident.get("root_cause", "Network Anomaly"),
                        "severity": severity,
                        "affectedTowers": incident.get("affected_components", []),
                        "context": issue_context,
                    }
                )
                ai_detailed_analysis = ai_result.get("recommendations", "")
            except Exception as e:
                print(f"AI issue analysis error: {e}")

        issue = {
            "id": incident_id,
            "region": region,
            "title": issue_type["title"],
            "severity": severity,
            "description": issue_type["description"],
            "impactScore": f"{random.randint(60, 99)}%",
            "affectedTowers": incident.get(
                "affected_components", [f"Tower-{random.randint(1, 10)}"]
            ),
            "status": incident.get("status", "Active").title(),
            "agentTrace": self.AGENT_TRACE,
            "activeAgent": random.choice(self.AGENT_TRACE),
            "suggestedAction": suggested_action,
            "detailedAnalysis": ai_detailed_analysis
            or self._build_issue_analysis(incident),
            "remediationSteps": [
                action.get("action", "Review telemetry")
                for action in incident.get("remediation_actions", [])
            ]
            or ["Awaiting remediation recommendation"],
            "agentLogs": self._build_agent_logs(incident),
            "created_at": time.time(),
        }
        with self.lock:
            self.issue_registry[incident_id] = issue
        return issue

    def _build_issue_analysis(self, incident: Dict) -> str:
        return (
            "Principal Agent detected elevated risk across "
            f"{incident.get('affected_components', ['edge cluster'])[0]}. "
            "Automated evaluation recommends proactive remediation to prevent user impact."
        )

    def _build_agent_logs(self, incident: Dict) -> List[Dict]:
        now = datetime.utcnow()
        logs = []
        for idx, agent in enumerate(self.AGENT_TRACE):
            logs.append(
                {
                    "timestamp": (now - timedelta(seconds=idx * 15)).isoformat(),
                    "agent": agent,
                    "message": f"{agent} reviewed telemetry for incident {incident.get('incident_id', '')}",
                }
            )
        return logs

    def _serialize_issue(self, issue: Dict) -> Dict:
        public_issue = dict(issue)
        public_issue.pop("created_at", None)
        return public_issue

    def _suggest_action(self, severity: str) -> str:
        if severity == "critical":
            return "redeploy_agent"
        if severity == "high":
            return "restart_agent"
        return "reroute_traffic"

    def _cleanup_expired_issues(self) -> None:
        """Clean up old issues - resolved issues after 2 min, active after 15 min."""
        now = time.time()
        resolved_expiry = now - 120  # 2 minutes for resolved issues
        active_expiry = now - 900  # 15 minutes for active issues
        with self.lock:
            for issue_id, issue in list(self.issue_registry.items()):
                created_at = issue.get("created_at", 0)
                is_resolved = issue.get("status") == "Resolved"
                resolved_at = issue.get("resolved_at", 0)

                # Remove resolved issues after 2 minutes of resolution
                if is_resolved and resolved_at and resolved_at < resolved_expiry:
                    self.issue_registry.pop(issue_id, None)
                # Remove active issues after 15 minutes
                elif not is_resolved and created_at < active_expiry:
                    self.issue_registry.pop(issue_id, None)

    # ------------------------------------------------------------------
    # Remediation & resolutions
    # ------------------------------------------------------------------
    def trigger_remediation(
        self, issue_id: str, action: Optional[str] = None
    ) -> (Dict, Dict):
        with self.lock:
            issue = self.issue_registry.get(issue_id)
            if issue:
                # Mark as resolved instead of removing immediately
                issue["status"] = "Resolved"
                issue["resolved_at"] = time.time()
        action = action or "restart_agent"
        action = action if action in self.REMEDIATION_ACTIONS else "restart_agent"
        target_agent = (issue or {}).get("activeAgent", "principal_agent")
        if action == "redeploy_agent":
            result = redeploy_agent(target_agent)
        elif action == "reroute_traffic":
            towers = (issue or {}).get("affectedTowers", ["Tower-1", "Tower-2"])
            source = towers[0]
            target = towers[-1] if len(towers) > 1 else f"Tower-{random.randint(3, 10)}"
            result = reroute_traffic(source, target, percentage=random.randint(40, 90))
        else:
            result = restart_agent(target_agent)

        resolution = self._build_resolution_entry(issue, result)
        with self.lock:
            self.resolution_log.append(resolution)
        return result, resolution

    def _build_resolution_entry(self, issue: Optional[Dict], result: Dict) -> Dict:
        summary_issue = issue.get("title") if issue else "Ad-hoc remediation"
        region = issue.get("region") if issue else random.choice(self.DEFAULT_REGIONS)
        return {
            "id": f"resolution-{uuid4().hex[:6]}",
            "region": region,
            "timestamp": datetime.utcnow().isoformat(),
            "title": "Automated Remediation Completed",
            "summary": f"{summary_issue} resolved via {result.get('operation')}",
            "initiatingAgent": (issue or {}).get("activeAgent", "Principal Agent"),
            "actions": [
                result.get("message", "Remediation executed"),
                "Stability verification completed",
            ],
            "rollbackStatus": "Available" if result.get("success") else "Manual Review",
            "confidenceScore": f"{random.randint(85, 99)}%",
        }

    def get_resolutions(self, region: str, limit: int = 20) -> List[Dict]:
        with self.lock:
            items = [res for res in self.resolution_log if res.get("region") == region]
        if not items:
            items = [self._historical_resolution(region) for _ in range(min(5, limit))]
        return items[-limit:][::-1]

    def _historical_resolution(self, region: str) -> Dict:
        incident = generate_incident_report(f"HIST-{uuid4().hex[:4]}".upper())
        return {
            "id": f"resolution-{uuid4().hex[:6]}",
            "region": region,
            "timestamp": incident.get("resolved_at") or datetime.utcnow().isoformat(),
            "title": "Historical Remediation",
            "summary": incident.get("root_cause", "Stability event") + " mitigated",
            "initiatingAgent": random.choice(self.AGENT_TRACE),
            "actions": ["Applied policy fix", "Verified KPIs"],
            "rollbackStatus": "Available",
            "confidenceScore": f"{random.randint(80, 97)}%",
        }

    # ------------------------------------------------------------------
    # Agent status
    # ------------------------------------------------------------------
    def get_agent_statuses(self) -> List[Dict]:
        statuses = []
        for agent in self.agent_names:
            details = pa_get_agent_status(agent)
            statuses.append(
                {
                    "name": agent.replace("_", " ").title(),
                    "status": details.get("status", "active"),
                    "uptime": f"{details.get('uptime_seconds', 0) // 3600}h",
                    "metrics": details.get("metrics", {}),
                    "resource_usage": details.get("resource_usage", {}),
                }
            )
        return statuses
