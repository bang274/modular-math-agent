import React, { useRef, useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import { useSolve } from '../../hooks/useSolve';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import './ChatWindow.css';

const SUGGESTIONS = [
  'Giải phương trình: 2x + 5 = 13',
  'Tính diện tích hình tròn có bán kính 5cm',
  'Tìm x biết: (x - 3)^2 = 16',
];

export const ChatWindow: React.FC = () => {
  const activeId = useChatStore((s) => s.activeId);
  const conversations = useChatStore((s) => s.conversations);
  const addMessage = useChatStore((s) => s.addMessage);
  const updateMessage = useChatStore((s) => s.updateMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const setError = useChatStore((s) => s.setError);
  const { solveFromText } = useSolve();
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [activeConv?.messages.length]);

  const handleSuggestion = async (text: string) => {
    const userMsgId = Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    const assistantMsgId = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

    addMessage({ id: userMsgId, role: 'user', content: text, timestamp: Date.now(), status: 'success' });
    addMessage({ id: assistantMsgId, role: 'assistant', content: '', timestamp: Date.now(), status: 'processing' });
    setLoading(true);

    try {
      const response = await solveFromText(text);
      updateMessage(assistantMsgId, { results: response.results, sessionId: response.session_id, status: 'success' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Có lỗi xảy ra';
      updateMessage(assistantMsgId, { status: 'error', error: message });
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-window">
      {activeConv && activeConv.messages.length > 0 ? (
        <div className="chat-window__messages" ref={messagesContainerRef}>
          {activeConv.messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
        </div>
      ) : (
        <div className="chat-window__empty">
          <div className="chat-window__empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h3>Math AI Agent</h3>
          <p>Nhập đề bài toán bằng text hoặc upload ảnh để nhận lời giải chi tiết.</p>
          <div className="chat-window__suggestions">
            {SUGGESTIONS.map((suggestion, idx) => (
              <button
                key={idx}
                className="chat-window__suggestion-btn"
                onClick={() => handleSuggestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <ChatInput />
    </div>
  );
};
