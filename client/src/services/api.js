import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increased timeout for AI operations
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

// API methods
export const dashboardAPI = {
  // Get telemetry data
  getTelemetry: (region, startTime, endTime) => {
    return api.get("/api/telemetry", {
      params: { region, startTime, endTime },
    });
  },

  // Get active users data
  getActiveUsers: (region) => {
    return api.get(`/api/active-users/${region}`);
  },

  // Get issues
  getIssues: (region, status = "active") => {
    return api.get("/api/issues", {
      params: { region, status },
    });
  },

  // Trigger AI-powered remediation through Principal Agent
  triggerRemediation: (issueId, action, region = "us-east-1") => {
    return api.post("/api/remediation/trigger", {
      issueId,
      action,
      region,
    });
  },

  // Analyze issue using Principal Agent AI
  analyzeIssue: (issueId, issue, region = "us-east-1") => {
    return api.post("/api/issue/analyze", {
      issueId,
      issue,
      region,
    });
  },

  // Chat with AI about an issue
  chatWithAI: (
    message,
    context = "trace_dashboard",
    issueId = null,
    issue = null
  ) => {
    return api.post("/api/chat", {
      message,
      context,
      issueId,
      issue,
    });
  },

  // Get Principal Agent integration status
  getIntegrationStatus: () => {
    return api.get("/api/integration/status");
  },

  // Get resolution history
  getResolutions: (region, limit = 20) => {
    return api.get("/api/resolutions", {
      params: { region, limit },
    });
  },

  // Get system health
  getSystemHealth: (region) => {
    return api.get(`/api/health/${region}`);
  },

  // Get agent status
  getAgentStatus: () => {
    return api.get("/api/agents/status");
  },
};

export default api;
