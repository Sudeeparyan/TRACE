/**
 * TRACE AWS Configuration
 *
 * Frontend configuration for AWS-deployed TRACE system.
 * This replaces the local Flask backend configuration.
 */

// Environment configuration
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || "production";
const AWS_REGION = import.meta.env.VITE_AWS_REGION || "us-east-1";

// API Configuration - Replace with your deployed API Gateway URLs
export const AWS_CONFIG = {
  // REST API Gateway
  apiGateway: {
    // Update this after API Gateway deployment
    endpoint:
      import.meta.env.VITE_API_ENDPOINT ||
      `https://YOUR_API_ID.execute-api.${AWS_REGION}.amazonaws.com/${ENVIRONMENT}`,
    apiKey: import.meta.env.VITE_API_KEY || "", // Set in environment or .env file
  },

  // WebSocket API for real-time telemetry
  webSocket: {
    endpoint:
      import.meta.env.VITE_WS_ENDPOINT ||
      `wss://YOUR_WS_API_ID.execute-api.${AWS_REGION}.amazonaws.com/${ENVIRONMENT}`,
  },

  // Cognito (if using authentication)
  cognito: {
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "",
    clientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "",
    region: AWS_REGION,
  },

  // Environment
  environment: ENVIRONMENT,
  region: AWS_REGION,
};

// API Endpoints
export const API_ENDPOINTS = {
  // Agent chat
  agentChat: "/agent/chat",

  // Health monitoring
  systemHealth: "/health/system",
  regionHealth: (regionId) => `/health/region/${regionId}`,
  towerHealth: (towerId) => `/health/tower/${towerId}`,

  // Telemetry
  telemetryHistory: "/telemetry/history",

  // Remediation
  remediate: "/remediate",

  // Alerts
  alerts: "/alerts",
};

/**
 * Make API request to TRACE backend
 */
export async function traceApiRequest(endpoint, options = {}) {
  const url = `${AWS_CONFIG.apiGateway.endpoint}${endpoint}`;

  const headers = {
    "Content-Type": "application/json",
    "x-api-key": AWS_CONFIG.apiGateway.apiKey,
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`TRACE API Error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * Chat with TRACE Agent
 */
export async function chatWithAgent(message, sessionId = null, context = {}) {
  return traceApiRequest(API_ENDPOINTS.agentChat, {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId,
      context,
    }),
  });
}

/**
 * Get system health
 */
export async function getSystemHealth() {
  return traceApiRequest(API_ENDPOINTS.systemHealth);
}

/**
 * Get regional health
 */
export async function getRegionHealth(regionId) {
  return traceApiRequest(API_ENDPOINTS.regionHealth(regionId));
}

/**
 * Get tower health
 */
export async function getTowerHealth(towerId) {
  return traceApiRequest(API_ENDPOINTS.towerHealth(towerId));
}

/**
 * Get active alerts
 */
export async function getAlerts(severity = "all", region = null) {
  const params = new URLSearchParams();
  if (severity) params.append("severity", severity);
  if (region) params.append("region", region);

  const queryString = params.toString();
  const endpoint = queryString
    ? `${API_ENDPOINTS.alerts}?${queryString}`
    : API_ENDPOINTS.alerts;

  return traceApiRequest(endpoint);
}

/**
 * Execute remediation action
 */
export async function executeRemediation(action, towerId, parameters = {}) {
  return traceApiRequest(API_ENDPOINTS.remediate, {
    method: "POST",
    body: JSON.stringify({
      action,
      tower_id: towerId,
      parameters,
    }),
  });
}

/**
 * Get telemetry history
 */
export async function getTelemetryHistory(options = {}) {
  const params = new URLSearchParams();
  if (options.towerId) params.append("tower_id", options.towerId);
  if (options.metric) params.append("metric", options.metric);
  if (options.period) params.append("period", options.period);

  const queryString = params.toString();
  const endpoint = queryString
    ? `${API_ENDPOINTS.telemetryHistory}?${queryString}`
    : API_ENDPOINTS.telemetryHistory;

  return traceApiRequest(endpoint);
}

/**
 * WebSocket connection for real-time updates
 */
export class TRACEWebSocket {
  constructor(onMessage, onError, onClose) {
    this.ws = null;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.subscriptions = new Set();
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.ws = new WebSocket(AWS_CONFIG.webSocket.endpoint);

      this.ws.onopen = () => {
        console.log("TRACE WebSocket connected");
        this.reconnectAttempts = 0;

        // Re-subscribe to previous subscriptions
        this.subscriptions.forEach((sub) => {
          this.send({ action: "subscribe", ...sub });
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage?.(data);
        } catch (e) {
          console.error("WebSocket message parse error:", e);
        }
      };

      this.ws.onerror = (error) => {
        console.error("TRACE WebSocket error:", error);
        this.onError?.(error);
      };

      this.ws.onclose = (event) => {
        console.log("TRACE WebSocket closed:", event.code, event.reason);
        this.onClose?.(event);

        // Auto-reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.min(
            1000 * Math.pow(2, this.reconnectAttempts),
            30000,
          );
          console.log(`Reconnecting in ${delay}ms...`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (error) {
      console.error("WebSocket connection error:", error);
      this.onError?.(error);
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket not connected, queuing message");
    }
  }

  subscribe(options = {}) {
    const subscription = {
      type: options.type || "telemetry",
      tower_id: options.towerId,
      region: options.region,
    };

    this.subscriptions.add(JSON.stringify(subscription));
    this.send({ action: "subscribe", ...subscription });
  }

  unsubscribe(options = {}) {
    const subscription = {
      type: options.type || "telemetry",
      tower_id: options.towerId,
      region: options.region,
    };

    this.subscriptions.delete(JSON.stringify(subscription));
    this.send({ action: "unsubscribe", ...subscription });
  }

  disconnect() {
    this.maxReconnectAttempts = 0; // Prevent auto-reconnect
    this.ws?.close();
  }
}

export default AWS_CONFIG;
