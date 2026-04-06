import React, { useRef, useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import './ChatWindow.css';

export const ChatWindow: React.FC = () => {
  const activeId = useChatStore((s) => s.activeId);
  const conversations = useChatStore((s) => s.conversations);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages.length]);

  return (
    <div className="chat-window">
      {activeConv && activeConv.messages.length > 0 ? (
        <div className="chat-window__messages">
          {activeConv.messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
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
            <span className="chat-window__suggestion">Tính tích phân ∫₀¹ x² dx</span>
            <span className="chat-window__suggestion">Giải phương trình x² + 2x - 3 = 0</span>
            <span className="chat-window__suggestion">Tìm đạo hàm f(x) = sin(x²)</span>
          </div>
        </div>
      )}

      <ChatInput />
    </div>
  );
};
