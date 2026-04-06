import React from 'react';
import './StatusBadge.css';

interface Props {
  status: string;
  size?: 'sm' | 'md';
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  completed: { label: 'Hoàn thành', color: 'green' },
  partial: { label: 'Một phần', color: 'yellow' },
  processing: { label: 'Đang xử lý', color: 'blue' },
  failed: { label: 'Lỗi', color: 'red' },
  cached: { label: 'Cached', color: 'purple' },
  easy: { label: 'Dễ', color: 'green' },
  hard: { label: 'Khó', color: 'orange' },
  unknown: { label: '?', color: 'gray' },
};

export const StatusBadge: React.FC<Props> = ({ status, size = 'sm' }) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'gray' };
  return (
    <span className={`status-badge status-badge--${config.color} status-badge--${size}`}>
      {config.label}
    </span>
  );
};
