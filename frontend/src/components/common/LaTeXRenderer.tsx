/**
 * LaTeX Renderer using KaTeX.
 */
import React, { useRef, useEffect } from 'react';
import katex from 'katex';

interface Props {
  latex: string;
  displayMode?: boolean;
  className?: string;
}

export const LaTeXRenderer: React.FC<Props> = ({
  latex,
  displayMode = false,
  className = '',
}) => {
  const containerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (containerRef.current && latex) {
      try {
        katex.render(latex, containerRef.current, {
          displayMode,
          throwOnError: false,
          trust: true,
          strict: false,
        });
      } catch {
        // Fallback to raw text
        if (containerRef.current) {
          containerRef.current.textContent = latex;
        }
      }
    }
  }, [latex, displayMode]);

  if (!latex) return null;

  return <span ref={containerRef} className={`latex-render ${className}`} />;
};
