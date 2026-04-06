import React from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/api';
import { SolutionCard } from '../solve/SolutionCard';
import { ErrorBoundary } from '../common/ErrorBoundary';
import './ChatMessage.css';

interface Props {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'chat-message--user' : 'chat-message--bot'}`}>
      {!isUser && (
        <div className="chat-message__avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
      )}

      <div className="chat-message__content">
        {isUser && message.content && (
          <div className="chat-message__text">{message.content}</div>
        )}

        {isUser && message.images && (
          <div className="chat-message__images">
            {message.images.map((img, idx) => (
              <img key={idx} src={img.preview} alt={`User upload ${idx + 1}`} />
            ))}
          </div>
        )}

        {!isUser && (message.status === 'processing') && (
          <div className="chat-message__typing">
            <span />
            <span />
            <span />
          </div>
        )}

        {!isUser && (message.status === 'error') && (
          <div className="chat-message__error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{message.error || 'Có lỗi xảy ra khi xử lý. Vui lòng thử lại.'}</span>
          </div>
        )}

        {!isUser && (message.status === 'success') && message.results && message.results.length > 0 && (
          <div className="chat-message__results">
            {message.results.map((result) => (
              <ErrorBoundary key={result.problem_id}>
                <SolutionCard result={result} />
              </ErrorBoundary>
            ))}
          </div>
        )}

        <span className="chat-message__time">
          {new Date(message.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};
