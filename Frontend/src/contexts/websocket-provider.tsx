import React, { createContext, useContext, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import ReconnectingWebSocket from 'reconnecting-websocket';

// Define query keys for different features
export const QUERY_KEYS = {
  DASHBOARD_METRICS: ['dashboard_metrics'] as const,
} as const;

type QueryKey = typeof QUERY_KEYS[keyof typeof QUERY_KEYS];

interface WebSocketContextType {
  requestRefresh: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketMessage {
  type?: string;
  timestamp?: string;
  data?: any;
  metrics?: any;
}

export interface DashboardMetrics {
  habits: {
    total: number;
    completed: number;
  };
  todos: {
    total: number;
    completed: number;
  };
  tasks: {
    total: number;
    completed: number;
  };
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const wsRef = useRef<ReconnectingWebSocket | null>(null);

  const handleMetricsUpdate = (metrics: DashboardMetrics) => {
    console.log('Updating dashboard metrics from WebSocket:', metrics);
    
    // Force React Query to recognize this as a new object to ensure subscribers detect the update
    const metricsWithTimestamp = {
      ...metrics,
      _timestamp: Date.now() // Add timestamp to ensure object reference changes
    };
    
    // Update the cache with the new metrics data
    queryClient.setQueryData(QUERY_KEYS.DASHBOARD_METRICS, metricsWithTimestamp);
  };

  const handleWebSocketMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'initial_metrics':
        console.log('Received initial metrics from WebSocket');
        if (data.data) {
          console.log('Initial metrics data:', data.data);
          handleMetricsUpdate(data.data);
        } else {
          console.warn('Initial metrics message missing data field');
        }
        break;
      case 'cache_invalidate':
        console.log('Received updated metrics from WebSocket');
        if (data.metrics) {
          console.log('Updated metrics data:', data.metrics);
          handleMetricsUpdate(data.metrics);
        } else {
          console.warn('Cache invalidate message missing metrics field');
        }
        break;
      default:
        // Ignore other message types
        break;
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      console.error('No auth token found in localStorage');
      return;
    }

    const url = `ws://localhost:8001/ws/dashboard?token=${encodeURIComponent(token)}`;
    console.log('Attempting to connect to WebSocket:', url);
    const ws = new ReconnectingWebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      ws.send(JSON.stringify({ type: 'ping' }));
    };

    ws.onerror = (error) => {
      console.error('WebSocket error occurred:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', data.type);
        handleWebSocketMessage(data);
      } catch (err) {
        console.error('Failed to parse WS message:', event.data);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    // Set up ping interval
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [queryClient]);

  const requestRefresh = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('Sending refresh request to WebSocket server');
      wsRef.current.send(JSON.stringify({ type: 'refresh' }));
    } else {
      console.warn('Cannot request refresh - WebSocket not connected');
    }
  };

  return (
    <WebSocketContext.Provider value={{ requestRefresh }}>
      {children}
    </WebSocketContext.Provider>
  );
} 