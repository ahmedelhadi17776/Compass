import React, { createContext, useContext, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ReconnectingWebSocket from "reconnecting-websocket";

// Define query keys for different features
export const QUERY_KEYS = {
  DASHBOARD_METRICS: ["dashboard_metrics"] as const,
} as const;

interface WebSocketContextType {
  requestRefresh: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
};

interface WebSocketMessage {
  type?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  requires_refresh?: boolean;
}

interface NotesMetrics {
  mood?: string;
  notes?: {
    count: number;
    recent: Array<{
      _id: string;
      title: string;
      content: string;
      updatedAt: string;
    }>;
  };
  journals?: {
    count: number;
    recent: Array<{
      _id: string;
      title: string;
      date: string;
      content: string;
      mood: string;
    }>;
  };
}

export interface DashboardMetrics {
  habits?: {
    total: number;
    completed: number;
  };
  todos?: {
    total: number;
    completed: number;
  };
  tasks?: {
    total: number;
    completed: number;
  };
  mood?: string;
  notes?: {
    count: number;
    recent: Array<{
      _id: string;
      title: string;
      content: string;
      updatedAt: string;
    }>;
  };
  journals?: {
    count: number;
    recent: Array<{
      _id: string;
      title: string;
      date: string;
      content: string;
      mood: string;
    }>;
  };
  calendar?: Record<string, unknown>;
  focus?: Record<string, unknown>;
  ai_usage?: Record<string, unknown>;
  system_metrics?: Record<string, unknown>;
  goals?: Record<string, unknown>;
  user?: Record<string, unknown>;
  cost?: Record<string, unknown>;
  _timestamp?: number;
  _wsUpdate?: boolean;
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const wsRef = useRef<ReconnectingWebSocket | null>(null);

  const handleMetricsUpdate = (metrics: DashboardMetrics) => {
    console.log("Updating dashboard metrics from WebSocket:", metrics);

    // Force React Query to recognize this as a new object to ensure subscribers detect the update
    const metricsWithTimestamp = {
      ...metrics,
      _timestamp: Date.now(), // Add timestamp to ensure object reference changes
      _wsUpdate: true, // Mark as WebSocket update
    };

    queryClient.setQueryData(
      QUERY_KEYS.DASHBOARD_METRICS,
      metricsWithTimestamp
    );

    console.log("Dashboard metrics updated via WebSocket");
  };

  const handleWebSocketMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case "initial_metrics":
        console.log("Received initial metrics from WebSocket");
        if (data.data) {
          console.log("Initial metrics data:", data.data);
          handleMetricsUpdate(data.data as unknown as DashboardMetrics);
        } else {
          console.warn("Initial metrics message missing data field");
        }
        break;
      case "dashboard_update":
        // New consolidated update message - acknowledge and request fresh data
        console.log(
          "Dashboard updated - acknowledging and requesting fresh metrics",
          data.data
        );
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "dashboard_update_ack" }));
        }
        break;
      case "fresh_metrics":
        console.log("Received fresh metrics from WebSocket");
        if (data.data) {
          console.log("Fresh metrics data:", data.data);
          handleMetricsUpdate(data.data as unknown as DashboardMetrics);
        } else {
          console.warn("Fresh metrics message missing data field");
        }
        break;
      case "metrics_update":
        console.log(
          "Received partial metrics update from WebSocket (Notes server)"
        );
        if (data.data && data.data.metrics) {
          // This is partial data from Notes server - merge with existing cache
          const currentData = queryClient.getQueryData<DashboardMetrics>(
            QUERY_KEYS.DASHBOARD_METRICS
          );

          if (currentData) {
            const notesMetrics = data.data.metrics as NotesMetrics;
            const updatedData = {
              ...currentData,
              // Only update the Notes server fields
              ...(notesMetrics.mood && { mood: notesMetrics.mood }),
              ...(notesMetrics.notes && { notes: notesMetrics.notes }),
              ...(notesMetrics.journals && { journals: notesMetrics.journals }),
              _timestamp: Date.now(),
              _wsUpdate: true,
            };

            queryClient.setQueryData(QUERY_KEYS.DASHBOARD_METRICS, updatedData);

            console.log("Merged partial metrics update with existing data");
          } else {
            console.warn(
              "No existing metrics data to merge with - ignoring partial update"
            );
          }
        } else {
          console.warn("Metrics update message missing data field");
        }
        break;
      case "error":
        console.error("WebSocket error:", data);
        break;
      case "connected":
      case "pong":
      case "ping":
        // Connection messages - just log
        console.debug(`WebSocket ${data.type} message`);
        break;
      default:
        // Log unhandled message types for debugging
        console.debug("❓ Unhandled WebSocket message type:", data.type, data);
        break;
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("No auth token found in localStorage");
      return;
    }

    const url = `ws://localhost:8001/ws/dashboard?token=${encodeURIComponent(
      token
    )}`;
    console.log("Attempting to connect to WebSocket:", url);
    const ws = new ReconnectingWebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      ws.send(JSON.stringify({ type: "ping" }));
    };

    ws.onerror = (error) => {
      console.error("WebSocket error occurred:", error);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log("WebSocket message received:", data.type);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error("Failed to parse WS message:", event.data, error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };

    // Set up ping interval
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [queryClient]);

  const requestRefresh = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("Sending refresh request to WebSocket server");
      wsRef.current.send(JSON.stringify({ type: "refresh" }));
    } else {
      console.warn("Cannot request refresh - WebSocket not connected");
    }
  };

  return (
    <WebSocketContext.Provider value={{ requestRefresh }}>
      {children}
    </WebSocketContext.Provider>
  );
}
