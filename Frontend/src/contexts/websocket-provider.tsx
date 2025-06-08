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
  event?: string;
  timestamp?: string;
  message?: string;
  data?: any;
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const wsRef = useRef<ReconnectingWebSocket | null>(null);

  const handleDashboardEvent = async (eventType: string) => {
    switch (eventType) {
      case 'dashboard_update':
      case 'metrics_update':
      case 'cache_invalidate':
      case 'user_activity':
        console.log('Received dashboard event:', eventType);
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.DASHBOARD_METRICS });
        break;
      default:
        console.warn('Unknown event type:', eventType);
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

    ws.onmessage = async (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        if (data.type === 'connected') {
          console.log('WebSocket connection confirmed:', data.message);
        }
        else if (data.type === 'pong') {
          console.log('Received pong from server');
        }
        else if (data.type) {
          await handleDashboardEvent(data.type);
        }
        else if (data.event) {
          await handleDashboardEvent(data.event);
        }
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
      wsRef.current.send(JSON.stringify({ type: 'refresh' }));
    }
  };

  return (
    <WebSocketContext.Provider value={{ requestRefresh }}>
      {children}
    </WebSocketContext.Provider>
  );
} 