import type { WSMessage } from '../types/api';

type MessageHandler = (message: WSMessage) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(sessionId: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}/api/v1/ws/${sessionId}`;
  }

  connect(): void {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => { this.reconnectAttempts = 0; };
    this.ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        this.handlers.forEach((h) => h(msg));
      } catch { /* ignore parse errors */ }
    };
    this.ws.onclose = () => this._tryReconnect();
    this.ws.onerror = (e) => console.error('[WS] Error:', e);
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(data));
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.push(handler);
    return () => { this.handlers = this.handlers.filter((h) => h !== handler); };
  }

  disconnect(): void {
    this.maxReconnectAttempts = 0;
    this.ws?.close();
    this.ws = null;
  }

  private _tryReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(), delay);
  }
}
