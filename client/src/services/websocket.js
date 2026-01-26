import { io } from "socket.io-client";

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(onConnect) {
    if (this.socket?.connected) {
      return;
    }

    // Connect to WebSocket server
    this.socket = io("http://localhost:8000", {
      transports: ["websocket"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      if (onConnect) onConnect();
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
    });

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error);
    });

    // Set up event listeners
    this.setupListeners();
  }

  setupListeners() {
    const events = [
      "telemetry",
      "activeUsers",
      "issue",
      "resolution",
      "health",
    ];

    events.forEach((event) => {
      this.socket.on(event, (data) => {
        const listeners = this.listeners.get(event) || [];
        listeners.forEach((callback) => callback(data));
      });
    });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;

    const listeners = this.listeners.get(event);
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  subscribeToRegion(region) {
    if (this.socket?.connected) {
      this.socket.emit("subscribe", { region });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export { WebSocketService };
