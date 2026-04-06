/**
 * Custom hook for WebSocket connection.
 */
import { useEffect, useRef, useCallback } from 'react';
import { WebSocketManager } from '../api/websocket';
import { useSolveStore } from '../store/solveStore';
import type { WSMessage } from '../types/api';

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocketManager | null>(null);
  const addWSMessage = useSolveStore((s) => s.addWSMessage);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocketManager(sessionId);
    wsRef.current = ws;

    ws.onMessage((msg: WSMessage) => {
      addWSMessage(msg);
    });

    ws.connect();

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [sessionId, addWSMessage]);

  const sendSolve = useCallback((text?: string, imageB64?: string) => {
    wsRef.current?.send({ action: 'solve', text, image_b64: imageB64 });
  }, []);

  return { sendSolve };
}
