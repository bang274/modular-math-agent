/**
 * SolutionCard — Displays a single problem's solution with steps and tool trace.
 */
import React, { useState } from 'react';
import type { ProblemResult } from '../../types/api';
import { LaTeXRenderer } from '../common/LaTeXRenderer';
import { StatusBadge } from '../common/StatusBadge';
import './SolutionCard.css';

interface Props {
  result: ProblemResult;
}

export const SolutionCard: React.FC<Props> = ({ result }) => {
  const [expanded, setExpanded] = useState(true);

  const routeLabel: Record<string, string> = {
    llm_direct: '🧠 LLM Direct',
    wolfram: '🔬 Wolfram Alpha',
    python_sandbox: '🐍 Python Sandbox',
    web_search: '🔍 Web Search',
    fallback_search: '🔍 Fallback Search',
    cached: '⚡ Cached',
    failed: '❌ Failed',
  };

  const confidenceColor = result.confidence >= 0.8 ? '#34d399' :
    result.confidence >= 0.5 ? '#fbbf24' : '#f87171';

  return (
    <div className={`solution-card ${result.error ? 'solution-card--error' : ''}`}>
      <div className="solution-card__header" onClick={() => setExpanded(!expanded)}>
        <div className="solution-card__title">
          <span className="solution-card__id">Bài {result.problem_id}</span>
          <StatusBadge status={result.difficulty} />
          {result.tool_trace.cache_hit && <StatusBadge status="cached" />}
        </div>
        <div className="solution-card__meta">
          <span className="solution-card__route">
            {routeLabel[result.tool_trace.route] || result.tool_trace.route}
          </span>
          <span className="solution-card__latency">
            {result.tool_trace.latency_ms}ms
          </span>
          <span className="solution-card__expand">{expanded ? '▾' : '▸'}</span>
        </div>
      </div>

      {expanded && (
        <div className="solution-card__body">
          <div className="solution-card__problem">
            <span className="label">Đề bài:</span>
            <LaTeXRenderer latex={result.original} displayMode />
          </div>

          {result.steps.length > 0 && (
            <div className="solution-card__steps">
              <span className="label">Lời giải:</span>
              {result.steps.map((step) => (
                <div key={step.step} className="solution-step">
                  <span className="step-number">{step.step}</span>
                  <div className="step-content">
                    <p className="step-desc">{step.description}</p>
                    {step.latex && <LaTeXRenderer latex={step.latex} displayMode />}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.final_answer && (
            <div className="solution-card__answer">
              <span className="label">Đáp án:</span>
              <div className="answer-box">
                <LaTeXRenderer latex={result.final_answer} displayMode />
              </div>
            </div>
          )}

          <div className="solution-card__footer">
            <div className="confidence-bar">
              <span className="confidence-label">Confidence:</span>
              <div className="confidence-track">
                <div
                  className="confidence-fill"
                  style={{
                    width: `${result.confidence * 100}%`,
                    backgroundColor: confidenceColor,
                  }}
                />
              </div>
              <span className="confidence-value" style={{ color: confidenceColor }}>
                {(result.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {result.tool_trace.tools_used.length > 0 && (
              <div className="tools-used">
                {result.tool_trace.tools_used.map((tool) => (
                  <span key={tool} className="tool-tag">{tool}</span>
                ))}
              </div>
            )}
          </div>

          {result.error && (
            <div className="solution-card__error">
              ⚠️ {result.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
