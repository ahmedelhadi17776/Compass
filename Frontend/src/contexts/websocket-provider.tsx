import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import ReconnectingWebSocket from "reconnecting-websocket";

// Define query keys for different features
export const QUERY_KEYS = {
  DASHBOARD_METRICS: ["dashboard_metrics"] as const,
} as const;

interface WebSocketContextType {
  requestRefresh: () => void;
  isConnected: boolean;
  sendMessage?: (message: Record<string, unknown>) => void;
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
  daily_timeline?: Array<{
    id: string;
    title: string;
    start_time: string;
    end_time?: string;
    type: string;
    is_completed: boolean;
  }>;
  habit_heatmap?: Record<string, number>;
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
  const isConnectedRef = useRef<boolean>(false);
  const pendingAckRef = useRef<boolean>(false);
  // Add debounce tracking
  const lastUpdateRef = useRef<number>(0);
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMetricsUpdate = useCallback(
    (metrics: DashboardMetrics) => {
      // Implement debouncing - only update if not too frequent (100ms minimum gap)
      const now = Date.now();
      if (now - lastUpdateRef.current < 100) {
        // If updates are coming too quickly, debounce them
        if (updateTimeoutRef.current) {
          clearTimeout(updateTimeoutRef.current);
        }

        updateTimeoutRef.current = setTimeout(() => {
          lastUpdateRef.current = Date.now();
          queryClient.setQueryData(QUERY_KEYS.DASHBOARD_METRICS, {
            ...metrics,
            _timestamp: Date.now(),
            _wsUpdate: true,
          });

          // Only invalidate if needed to avoid unnecessary fetches
          queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.DASHBOARD_METRICS,
          });
        }, 100);
        return;
      }

      // Update timestamp to track the latest update
      lastUpdateRef.current = now;

      // Force React Query to recognize this as a new object to ensure subscribers detect the update
      const metricsWithTimestamp = {
        ...metrics,
        _timestamp: now,
        _wsUpdate: true,
      };

      queryClient.setQueryData(
        QUERY_KEYS.DASHBOARD_METRICS,
        metricsWithTimestamp
      );

      // Invalidate queries to trigger immediate re-fetch for dependent components
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.DASHBOARD_METRICS,
      });
    },
    [queryClient]
  );

  const handleWebSocketMessage = useCallback(
    (data: WebSocketMessage) => {
      // Only log important messages to reduce console noise
      const logMessage = data.type !== "ping" && data.type !== "pong";

      switch (data.type) {
        case "connected":
          console.log("WebSocket connection confirmed");
          isConnectedRef.current = true;
          break;

        case "initial_metrics":
          if (data.data) {
            handleMetricsUpdate(data.data as unknown as DashboardMetrics);
          }
          break;

        case "dashboard_update":
          // New consolidated update message - acknowledge immediately for rapid response
          // Prevent duplicate acknowledgments
          if (
            !pendingAckRef.current &&
            wsRef.current?.readyState === WebSocket.OPEN
          ) {
            pendingAckRef.current = true;
            wsRef.current.send(
              JSON.stringify({ type: "dashboard_update_ack" })
            );

            // Reset pending flag after a short delay
            setTimeout(() => {
              pendingAckRef.current = false;
            }, 100);
          }
          break;

        case "fresh_metrics":
          if (data.data) {
            handleMetricsUpdate(data.data as unknown as DashboardMetrics);
          }
          break;

        case "metrics_update":
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
                ...(notesMetrics.journals && {
                  journals: notesMetrics.journals,
                }),
                _timestamp: Date.now(),
                _wsUpdate: true,
              };

              queryClient.setQueryData(
                QUERY_KEYS.DASHBOARD_METRICS,
                updatedData
              );
            } else if (logMessage) {
              // Less noisy approach
              console.debug(
                "No existing metrics data to merge with - ignoring partial update"
              );
            }
          } else if (logMessage) {
            // Reduce console noise for expected behavior
            console.debug(
              "Metrics update without data field - normal for some updates"
            );
          }
          break;

        case "error":
          console.error("WebSocket error:", data);
          break;

        case "pong":
          // Connection health check response - don't log
          break;

        case "ping":
          // Server ping - respond with pong, don't log
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "pong" }));
          }
          break;

        default:
          // Only log non-regular messages for debugging
          if (logMessage) {
            console.debug("Unhandled WebSocket message type:", data.type);
          }
          break;
      }
    },
    [handleMetricsUpdate, queryClient]
  );

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("No auth token found in localStorage");
      return;
    }

    const url = `ws://localhost:8001/ws/dashboard?token=${encodeURIComponent(
      token
    )}`;

    const ws = new ReconnectingWebSocket(url, [], {
      connectionTimeout: 3000,
      maxRetries: 10,
      maxReconnectionDelay: 5000,
      minReconnectionDelay: 500,
      reconnectionDelayGrowFactor: 1.2,
    });
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      isConnectedRef.current = true;
      ws.send(JSON.stringify({ type: "ping" }));
    };

    ws.onerror = (error) => {
      console.error("WebSocket error occurred:", error);
      isConnectedRef.current = false;
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        // Don't log ping/pong messages to reduce noise
        if (data.type !== "ping" && data.type !== "pong") {
          console.log("WebSocket message received:", data.type);
        }

        handleWebSocketMessage(data);
      } catch (error) {
        console.error("Failed to parse WS message:", event.data, error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      isConnectedRef.current = false;
    };

    // Set up ping interval
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);

    return () => {
      clearInterval(pingInterval);
      isConnectedRef.current = false;
      // Clear any pending updates
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
      ws.close();
    };
  }, [handleWebSocketMessage]);

  const requestRefresh = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("Sending refresh request to WebSocket server");
      wsRef.current.send(JSON.stringify({ type: "refresh" }));
    } else {
      console.warn("Cannot request refresh - WebSocket not connected");
    }
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("Cannot send message - WebSocket not connected");
    }
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        requestRefresh,
        isConnected: isConnectedRef.current,
        sendMessage,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}
