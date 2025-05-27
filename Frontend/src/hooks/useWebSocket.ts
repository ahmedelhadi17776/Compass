import { useEffect, useRef, useState } from 'react';

interface Notification {
  id: string;
  title: string;
  message?: string; // Optional for backward compatibility
  content?: string; // From server format
  type: 'info' | 'success' | 'warning' | 'error' | string;
  status?: string;
  createdAt: string;
  read: boolean;
}

export const useWebSocket = (token: string | null) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    const connect = () => {
      ws.current = new WebSocket(`ws://localhost:8000/api/notifications/ws?token=${token}`);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket Connected');
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle count message type
          if (data.type === 'count') {
            console.log(`You have ${data.count} unread notifications`);
            return;
          }
          
          // Only process valid notifications with an ID
          if (data.id) {
            // Normalize the notification format
            const notification: Notification = {
              id: data.id,
              title: data.title || 'Notification',
              message: data.message || data.content || '', // Handle both formats
              type: data.type || 'info',
              createdAt: data.createdAt || new Date().toISOString(),
              read: data.status === 'read' || false
            };
            
            setNotifications((prev) => {
              // Check if notification already exists to avoid duplicates
              const exists = prev.some(n => n.id === notification.id);
              if (exists) {
                return prev;
              }
              return [notification, ...prev];
            });
          }
        } catch (err) {
          console.error('Error parsing notification:', err);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connect, 5000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.current?.close();
      };
    };

    connect();

    return () => {
      ws.current?.close();
    };
  }, [token]);

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
    
    // Send command to server to mark as read
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        command: 'mark_read',
        id: id
      }));
    }
  };

  const clearNotifications = () => {
    setNotifications(prev => prev.map(notification => ({ ...notification, read: true })));
    
    // Send command to server to mark all as read
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        command: 'mark_all_read'
      }));
    }
  };

  return {
    notifications,
    isConnected,
    markAsRead,
    clearNotifications
  };
}; 