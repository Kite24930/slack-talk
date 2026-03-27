import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/appStore';

const WS_URL = 'ws://127.0.0.1:9321';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const store = useAppStore();

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        store.setConnected(true);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
          case 'message':
            store.addMessage(msg.data.channel_id, msg.data);
            break;
          case 'voice_state':
            store.setVoiceState(msg.data.state);
            break;
          case 'channels':
            store.setChannels(msg.data);
            break;
        }
      };

      ws.onclose = () => {
        store.setConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connect, 3000);
      };

      wsRef.current = ws;
    };

    connect();
    return () => wsRef.current?.close();
  }, []);

  return { send };
}
