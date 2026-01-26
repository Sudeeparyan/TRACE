// Mock data generator for demo purposes
// Can be used when backend is not available

export const generateMockTelemetry = () => {
  const baseEnergy = 50 + Math.random() * 30;
  const baseCongestion = 40 + Math.random() * 40;
  const baseAnomaly = Math.random() * 50;

  return {
    timestamp: Date.now(),
    energy: baseEnergy + Math.sin(Date.now() / 10000) * 10,
    congestion: baseCongestion + Math.sin(Date.now() / 8000) * 15,
    anomaly_score: baseAnomaly,
    traffic_load: 50 + Math.random() * 40,
    trx_utilization: 60 + Math.random() * 30,
    power_draw: 80 + Math.random() * 40,
  };
};

export const generateMockActiveUsers = () => {
  const base = 10000;
  const variance = 3000;
  const time = Date.now();

  return {
    timestamp: time,
    activeUsers: base + Math.sin(time / 30000) * variance + Math.random() * 500,
    towerCluster: `Tower-${Math.floor(Math.random() * 5) + 1}`,
    lastOptimization: Math.random() > 0.8 ? "Load Balancing" : "None",
    surgeDetected: Math.random() > 0.95,
  };
};

export const generateMockIssue = () => {
  const severities = ["critical", "high", "medium", "low"];
  const titles = [
    "High Congestion Detected",
    "TRX Utilization Exceeded",
    "Power Anomaly",
    "Network Latency Spike",
    "Resource Exhaustion",
  ];
  const agents = [
    "Monitoring",
    "Prediction",
    "Decision xApp",
    "Action",
    "Learning",
  ];

  return {
    id: `issue-${Date.now()}-${Math.random()}`,
    title: titles[Math.floor(Math.random() * titles.length)],
    severity: severities[Math.floor(Math.random() * severities.length)],
    description:
      "Automated detection identified an anomaly requiring attention.",
    affectedTowers: [`Tower-${Math.floor(Math.random() * 10) + 1}`],
    impactScore: `${Math.floor(Math.random() * 50) + 50}%`,
    status: "Active",
    agentTrace: agents,
    activeAgent: agents[Math.floor(Math.random() * agents.length)],
    suggestedAction: "restart_agent",
    detailedAnalysis:
      "System metrics indicate elevated resource usage patterns.",
    remediationSteps: [
      "Identify root cause from telemetry data",
      "Execute automated remediation",
      "Verify system stability",
      "Update learning model",
    ],
    agentLogs: [
      {
        timestamp: new Date().toISOString(),
        agent: "Monitoring",
        message: "Anomaly detected",
      },
      {
        timestamp: new Date().toISOString(),
        agent: "Prediction",
        message: "Analyzing trends",
      },
      {
        timestamp: new Date().toISOString(),
        agent: "Decision xApp",
        message: "Recommending action",
      },
    ],
  };
};

export const generateMockResolution = () => {
  return {
    id: `resolution-${Date.now()}-${Math.random()}`,
    timestamp: Date.now(),
    title: "Automated Remediation Completed",
    summary:
      "System restored to normal operation through automated intervention.",
    initiatingAgent: "Principal Agent",
    actions: [
      "Restarted affected TRX units",
      "Redistributed traffic load",
      "Verified system stability",
    ],
    rollbackStatus: "Available",
    learningNotes: "Pattern recorded for future optimization",
    confidenceScore: `${Math.floor(Math.random() * 15) + 85}%`,
  };
};

// Mock WebSocket simulator
export class MockWebSocketService {
  constructor() {
    this.intervals = [];
    this.listeners = new Map();
  }

  connect(onConnect) {
    console.log("Mock WebSocket connected");
    if (onConnect) onConnect();
    this.startMockStreams();
  }

  startMockStreams() {
    // Telemetry stream (every 1 second)
    this.intervals.push(
      setInterval(() => {
        this.emit("telemetry", generateMockTelemetry());
      }, 1000)
    );

    // Active users stream (every 2 seconds)
    this.intervals.push(
      setInterval(() => {
        this.emit("activeUsers", generateMockActiveUsers());
      }, 2000)
    );

    // Random issues (every 30 seconds)
    this.intervals.push(
      setInterval(() => {
        if (Math.random() > 0.7) {
          this.emit("issue", generateMockIssue());
        }
      }, 30000)
    );

    // Health updates (every 5 seconds)
    this.intervals.push(
      setInterval(() => {
        this.emit("health", {
          score: 85 + Math.random() * 15,
          status: Math.random() > 0.2 ? "Operational" : "Degraded",
        });
      }, 5000)
    );
  }

  emit(event, data) {
    const listeners = this.listeners.get(event) || [];
    listeners.forEach((callback) => callback(data));
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  subscribeToRegion(region) {
    console.log(`Subscribed to region: ${region}`);
  }

  disconnect() {
    this.intervals.forEach((interval) => clearInterval(interval));
    this.intervals = [];
    console.log("Mock WebSocket disconnected");
  }
}
