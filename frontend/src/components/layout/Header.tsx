import React from 'react';
import { useChatStore } from '../../store/chatStore';
import './Header.css';

export const Header: React.FC = () => {
  const newConversation = useChatStore((s) => s.newConversation);

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div className="header-brand-text">
          <h1 className="header-title">Math AI Agent</h1>
          <span className="header-badge">Pipeline v1.0</span>
        </div>
      </div>
      <button className="header-new-chat" onClick={() => newConversation()}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Cuộc trò chuyện mới
      </button>
    </header>
  );
};
