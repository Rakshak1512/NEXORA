import React, { createContext, useContext, useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/api';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext();

export const getWebSocketUrl = () => {
  const configuredUrl = import.meta.env.VITE_API_URL;
  const fallbackUrl = import.meta.env.DEV ? API_BASE_URL : window.location.origin;
  const cleanBase = (configuredUrl || fallbackUrl).replace(/\/+$/, '').replace(/\/api$/, '');
  const wsProtocol = cleanBase.startsWith('https://') ? 'wss://' : 'ws://';
  const wsHost = cleanBase.replace(/^https?:\/\//, '');
  return wsProtocol + wsHost + '/ws';
};

export const WebSocketProvider = ({ children }) => {
  const { user } = useAuth();
  const token = user ? (localStorage.getItem('cynera_token') || localStorage.getItem('cicada_token')) : null;
  const [latestEvent, setLatestEvent] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let stopped = false;

    if (!token) {
      setIsConnected(false);
      setLatestEvent(null);
      return undefined;
    }

    const connect = () => {
      if (stopped) return;
      try {
        ws = new WebSocket(getWebSocketUrl());
        ws.onopen = () => ws.send(JSON.stringify({ type: 'AUTH', token }));

        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'AUTHENTICATED') {
              setIsConnected(true);
              return;
            }
            setLatestEvent(parsed);
          } catch (_) {
            // Ignore malformed server messages.
          }
        };

        ws.onclose = (event) => {
          setIsConnected(false);
          if (!stopped && event.code !== 4401 && event.code !== 4403) {
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };
        ws.onerror = () => {
          setIsConnected(false);
          try { ws.close(); } catch (_) {}
        };
      } catch (_) {
        setIsConnected(false);
        if (!stopped) reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    connect();
    return () => {
      stopped = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        try { ws.close(); } catch (_) {}
      }
      setIsConnected(false);
    };
  }, [token]);

  return (
    <WebSocketContext.Provider value={{ latestEvent, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
