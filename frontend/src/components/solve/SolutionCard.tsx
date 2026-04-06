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

  // Helper to render text containing inline math bounded by $
  const renderMixedText = (text: string) => {
    if (!text) return null;
    const parts = text.split(/(\$+[^$]+\$+)/g);
    return parts.map((part, index) => {
      if (part.startsWith('$') && part.endsWith('$')) {
        const cleanMath = part.replace(/\$/g, '');
        return <LaTeXRenderer key={index} latex={cleanMath} displayMode={false} />;
      }
      return <span key={index}>{part}</span>;
    });
  };

  const routeLabel: Record<string, string> = {
    llm_direct: '🧠 LLM Direct',
    wolfram: '🔬 Wolfram Alpha',
    python_sandbox: '🐍 Python Sandbox',
    web_search: '🔍 Web Search',
    fallback_search: '🔍 Fallback Search',
    cached: '⚡ Cached',
    unknown: '❓ Unknown',
    failed: '❌ Failed',
  };

  const route = result.tool_trace?.route || 'unknown';
  const cacheHit = result.tool_trace?.cache_hit || false;
  const latency = result.tool_trace?.latency_ms || 0;

  const confidenceColor = result.confidence >= 0.8 ? '#34d399' :
    result.confidence >= 0.5 ? '#fbbf24' : '#f87171';

  return (
    <div className={`solution-card ${result.error ? 'solution-card--error' : ''}`}>
      <div className="solution-card__header" onClick={() => setExpanded(!expanded)}>
        <div className="solution-card__title">
          <span className="solution-card__id">Bài {result.problem_id}</span>
          <StatusBadge status={result.difficulty || 'unknown'} />
          {cacheHit && <StatusBadge status="cached" />}
        </div>
        <div className="solution-card__meta">
          <span className="solution-card__route">
            {routeLabel[route] || route}
          </span>
          <span className="solution-card__latency">
            {latency}ms
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
                    <p className="step-desc">{renderMixedText(step.description)}</p>
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
                {result.final_answer.includes('\\') || result.final_answer.includes('^') || result.final_answer.includes('_') || result.final_answer.includes('$')
                  ? <LaTeXRenderer latex={result.final_answer} displayMode />
                  : <span className="answer-text">{renderMixedText(result.final_answer)}</span>
                }
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

            {result.tool_trace?.tools_used && result.tool_trace.tools_used.length > 0 && (
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
