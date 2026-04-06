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

  // Strip dollar signs if present
  const cleanLatex = latex
    .replace(/^\$+|\$+$/g, '')
    .replace(/^\$\$|\$\$$/g, '')
    .trim();

  useEffect(() => {
    if (containerRef.current && cleanLatex) {
      try {
        katex.render(cleanLatex, containerRef.current, {
          displayMode,
          throwOnError: false,
          trust: true,
          strict: false,
        });
      } catch {
        // Fallback to raw text
        if (containerRef.current) {
          containerRef.current.textContent = cleanLatex;
        }
      }
    }
  }, [cleanLatex, displayMode]);

  if (!cleanLatex) return null;

  return <span ref={containerRef} className={`latex-render ${className}`} />;
};
