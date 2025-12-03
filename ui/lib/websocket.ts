import { useEffect, useRef, useCallback } from 'react';
import { useTrackingStore } from './store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function useTrackingWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false);
  const updateLocation = useTrackingStore((state) => state.updateLocation);

  useEffect(() => {
    let isSubscribed = true;

    const connect = () => {
      // Prevent multiple simultaneous connection attempts
      if (!isSubscribed || isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
        return;
      }

      isConnectingRef.current = true;

      const ws = new WebSocket(`${WS_URL}/ws/tracking`);

      ws.onopen = () => {
        isConnectingRef.current = false;
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'location_update') {
            updateLocation(message.data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = () => {
        // Silently handle errors - onclose will handle reconnection
        isConnectingRef.current = false;
      };

      ws.onclose = () => {
        isConnectingRef.current = false;
        wsRef.current = null;

        // Attempt to reconnect after 3 seconds
        if (isSubscribed) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    };

    // Small delay to avoid React Strict Mode double-mount issues
    const initialTimeout = setTimeout(connect, 100);

    // Cleanup
    return () => {
      isSubscribed = false;
      clearTimeout(initialTimeout);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [updateLocation]);

  return wsRef.current;
}
