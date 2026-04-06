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

  // Extract first delimited math block if present: "text $...$" -> "..."
  const extractMath = (input: string): string => {
    const display = input.match(/\$\$([\s\S]+?)\$\$/);
    if (display?.[1]) return display[1].trim();

    const inline = input.match(/\$([^$]+)\$/);
    if (inline?.[1]) return inline[1].trim();

    return input.replace(/^\$+|\$+$/g, '').trim();
  };

  const cleanLatex = extractMath(latex || '');

  useEffect(() => {
    if (containerRef.current && cleanLatex) {
      try {
        katex.render(cleanLatex, containerRef.current, {
          displayMode,
          throwOnError: true,
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
