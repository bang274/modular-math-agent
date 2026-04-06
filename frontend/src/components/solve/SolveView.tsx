/**
 * SolveView — Main results display.
 */
import React from 'react';
import { useSolveStore } from '../../store/solveStore';
import { SolutionCard } from './SolutionCard';
import { StatusBadge } from '../common/StatusBadge';
import './SolveView.css';

export const SolveView: React.FC = () => {
  const { results, status, totalProblems, solvedCount, failedCount, cachedCount, totalLatencyMs, error } =
    useSolveStore();

  if (error) {
    return (
      <div className="solve-error">
        <span className="solve-error__icon">❌</span>
        <p>{error}</p>
      </div>
    );
  }

  if (results.length === 0) return null;

  return (
    <div className="solve-view">
      <div className="solve-summary">
        <div className="solve-summary__header">
          <h2>Kết quả</h2>
          <StatusBadge status={status} size="md" />
        </div>
        <div className="solve-stats">
          <div className="stat">
            <span className="stat-value">{totalProblems}</span>
            <span className="stat-label">Tổng bài</span>
          </div>
          <div className="stat stat--green">
            <span className="stat-value">{solvedCount}</span>
            <span className="stat-label">Đã giải</span>
          </div>
          {failedCount > 0 && (
            <div className="stat stat--red">
              <span className="stat-value">{failedCount}</span>
              <span className="stat-label">Lỗi</span>
            </div>
          )}
          {cachedCount > 0 && (
            <div className="stat stat--purple">
              <span className="stat-value">{cachedCount}</span>
              <span className="stat-label">Cached</span>
            </div>
          )}
          <div className="stat">
            <span className="stat-value">{(totalLatencyMs / 1000).toFixed(1)}s</span>
            <span className="stat-label">Thời gian</span>
          </div>
        </div>
      </div>

      <div className="solve-results">
        {results.map((result) => (
          <SolutionCard key={result.problem_id} result={result} />
        ))}
      </div>
    </div>
  );
};
