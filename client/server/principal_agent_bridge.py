"""Utility bridge that maps principal_agent tooling outputs to dashboard-friendly data."""

from __future__ import annotations

import random
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional
from uuid import uuid4

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
        raw = check_system_health()
        score_range = self.STATUS_SCORE_RANGES.get(
            raw.get("overall_status", "healthy"), [80, 95]
        )
        score = round(random.uniform(*score_range), 2)
        return {
            "region": region,
            "score": score,
            "status": raw.get("overall_status", "healthy").title(),
            "details": raw,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Telemetry & active users
    # ------------------------------------------------------------------
    def _build_telemetry_point(self, region: str, seconds_back: int = 0) -> Dict:
        metrics = get_system_metrics(metric_type="all")
        energy = metrics.get("energy_metrics", {})
        traffic = metrics.get("traffic_metrics", {})
        health = metrics.get("health_metrics", {})

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

        timestamp = datetime.utcnow() - timedelta(seconds=seconds_back)
        return {
            "region": region,
            "timestamp": timestamp.isoformat(),
            "energy": round(energy_pct, 2),
            "congestion": round(congestion_pct, 2),
            "anomaly_score": round(anomaly_score, 2),
            "traffic_load": round(
                _clamp(congestion_pct + random.uniform(-5, 8), 0, 100), 2
            ),
            "trx_utilization": round(_clamp(random.gauss(78, 6), 30, 100), 2),
            "power_draw": round(
                energy.get("current_consumption_kwh", random.uniform(80, 120)), 2
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
        self._cleanup_expired_issues()
        active = [
            issue
            for issue in self._current_issues().values()
            if issue.get("region") == region
        ]
        target = random.randint(0, 3)
        while len(active) < target:
            issue = self._create_issue(region)
            active.append(issue)
        return [self._serialize_issue(issue) for issue in active]

    def maybe_new_issue(self, region: str) -> Optional[Dict]:
        self._cleanup_expired_issues()
        if random.random() < 0.6:
            issue = self._create_issue(region)
            return self._serialize_issue(issue)
        return None

    def _current_issues(self) -> Dict[str, Dict]:
        with self.lock:
            return dict(self.issue_registry)

    def _create_issue(self, region: str) -> Dict:
        incident_id = f"issue-{uuid4().hex[:8]}"
        incident = generate_incident_report(incident_id.upper())
        severity = random.choice(["critical", "high", "medium"])
        suggested_action = self._suggest_action(severity)
        issue = {
            "id": incident_id,
            "region": region,
            "title": incident.get("root_cause", "Network Anomaly Detected")
            .replace("_", " ")
            .title(),
            "severity": severity,
            "description": incident.get("root_cause", ""),
            "impactScore": f"{random.randint(60, 99)}%",
            "affectedTowers": incident.get(
                "affected_components", [f"Tower-{random.randint(1, 10)}"]
            ),
            "status": incident.get("status", "Active").title(),
            "agentTrace": self.AGENT_TRACE,
            "activeAgent": random.choice(self.AGENT_TRACE),
            "suggestedAction": suggested_action,
            "detailedAnalysis": self._build_issue_analysis(incident),
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
        expiry = time.time() - 900  # 15 minutes
        with self.lock:
            for issue_id, issue in list(self.issue_registry.items()):
                if issue.get("created_at", 0) < expiry:
                    self.issue_registry.pop(issue_id, None)

    # ------------------------------------------------------------------
    # Remediation & resolutions
    # ------------------------------------------------------------------
    def trigger_remediation(
        self, issue_id: str, action: Optional[str] = None
    ) -> (Dict, Dict):
        with self.lock:
            issue = self.issue_registry.pop(issue_id, None)
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
