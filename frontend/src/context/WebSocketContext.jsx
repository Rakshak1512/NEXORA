import React, { createContext, useContext, useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/api';

const WebSocketContext = createContext();

export const getWebSocketUrl = () => {
  const cleanBase = (API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '').replace(/\/api$/, '');
  const wsProtocol = cleanBase.startsWith('https://') ? 'wss://' : 'ws://';
  const wsHost = cleanBase.replace(/^https?:\/\//, '');
  return `${wsProtocol}${wsHost}/ws`;
};

export const WebSocketProvider = ({ children }) => {
  const [latestEvent, setLatestEvent] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;

    const connect = () => {
      const wsUrl = getWebSocketUrl();
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            setLatestEvent(parsed);
          } catch (e) {
            // ignore malformed
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
          try { ws.close(); } catch (_) {}
        };
      } catch (err) {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      if (ws) {
        try { ws.close(); } catch (_) {}
      }
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ latestEvent, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
