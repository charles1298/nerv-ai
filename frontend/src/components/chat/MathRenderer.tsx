"use client";

// Renderiza texto com LaTeX inline ($...$) via KaTeX, conforme seção 5.1.

import katex from "katex";
import { useMemo } from "react";

interface MathRendererProps {
  content: string;
}

export function MathRenderer({ content }: MathRendererProps) {
  const parts = useMemo(() => content.split(/(\$[^$]+\$)/g), [content]);

  return (
    <span className="whitespace-pre-wrap">
      {parts.map((part, i) => {
        if (part.startsWith("$") && part.endsWith("$") && part.length > 2) {
          const latex = part.slice(1, -1);
          let html: string;
          try {
            html = katex.renderToString(latex, { throwOnError: true });
          } catch {
            return <span key={i}>{part}</span>;
          }
          return <span key={i} dangerouslySetInnerHTML={{ __html: html }} />;
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}
