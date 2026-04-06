import React from 'react';
import './Header.css';

export const Header: React.FC = () => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <span className="header-logo">🧠</span>
        <h1 className="header-title">Math AI Agent</h1>
        <span className="header-badge">Pipeline v1.0</span>
      </div>
      <nav className="header-nav">
        <a href="/" className="nav-link active">Solve</a>
        <a href="/history" className="nav-link">History</a>
      </nav>
    </header>
  );
};
