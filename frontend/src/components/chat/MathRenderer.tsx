"use client";

// Renderiza texto com LaTeX inline ($...$) via KaTeX, conforme seção 5.1.
// Fora da matemática, limpa marcação Markdown: a bolha não a interpreta e o
// aluno acabaria lendo os asteriscos.

import katex from "katex";
import { useMemo } from "react";

import { limparMarcacao } from "@/lib/text";

interface MathRendererProps {
  content: string;
}

/**
 * Marcador para o cifrão do real durante a separação.
 *
 * "R$ 27,00" é dinheiro, não delimitador de fórmula. Sem isolar esse cifrão ele
 * pareia com o próximo da frase e tudo que estiver no meio vira LaTeX — numa
 * questão de juros, troco ou desconto, meia frase saía renderizada como
 * fórmula, letra por letra. Usa um code point de uso privado, que não aparece
 * em texto real.
 */
const CIFRAO_REAL = "\uE000";

export function MathRenderer({ content }: MathRendererProps) {
  // `R\$` (já escapado para LaTeX) não casa aqui, porque tem a barra no meio —
  // então fórmula bem escrita passa intacta.
  const parts = useMemo(
    () => content.replace(/R\$/g, CIFRAO_REAL).split(/(\$[^$]+\$)/g),
    [content],
  );

  return (
    <span className="whitespace-pre-wrap">
      {parts.map((part, i) => {
        if (part.startsWith("$") && part.endsWith("$") && part.length > 2) {
          // Dentro da fórmula o cifrão volta escapado, que é como o LaTeX o escreve.
          const latex = part.slice(1, -1).split(CIFRAO_REAL).join("R\\$");
          let html: string;
          try {
            html = katex.renderToString(latex, { throwOnError: true });
          } catch {
            return <span key={i}>{part.split(CIFRAO_REAL).join("R$")}</span>;
          }
          return <span key={i} dangerouslySetInnerHTML={{ __html: html }} />;
        }
        return <span key={i}>{limparMarcacao(part.split(CIFRAO_REAL).join("R$"))}</span>;
      })}
    </span>
  );
}
