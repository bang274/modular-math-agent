import React from 'react';
import { useChatStore } from '../../store/chatStore';
import './Sidebar.css';

export const Sidebar: React.FC = () => {
  const conversations = useChatStore((s) => s.conversations);
  const activeId = useChatStore((s) => s.activeId);
  const setActive = useChatStore((s) => s.setActive);
  const newConversation = useChatStore((s) => s.newConversation);
  const deleteConversation = useChatStore((s) => s.deleteConversation);

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <h2 className="sidebar__title">Lịch sử</h2>
        <button className="sidebar__new" onClick={newConversation}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Mới
        </button>
      </div>

      <div className="sidebar__list">
        {conversations.length === 0 && (
          <p className="sidebar__empty">Chưa có cuộc trò chuyện nào</p>
        )}
        {[...conversations].reverse().map((conv) => (
          <div
            key={conv.id}
            className={`sidebar__item ${conv.id === activeId ? 'active' : ''}`}
            onClick={() => setActive(conv.id)}
          >
            <div className="sidebar__item-info">
              <span className="sidebar__item-title">{conv.title}</span>
              <span className="sidebar__item-date">
                {new Date(conv.updatedAt).toLocaleDateString('vi-VN')} · {conv.messages.length} tin nhắn
              </span>
            </div>
            <button
              className="sidebar__item-delete"
              onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
};
