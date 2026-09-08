"use client";

// Seção que existe na navegação mas ainda não tem backend.
//
// Deliberadamente sem dado de exemplo. O pacote de design traz essas telas
// preenchidas por um mock, e exibi-lo seria mostrar ao professor entregas,
// materiais e dúvidas que não existem — alguém tentaria lançar uma tarefa de
// verdade ali. Dizer o que a seção vai fazer, e que ainda não faz, é honesto e
// continua útil: o professor já entende o plano do produto.

import Link from "next/link";
import { ArrowLeft, type LucideIcon } from "lucide-react";
import { Reveal } from "./Reveal";

export function EmBreve({
  titulo,
  icone: Icone,
  descricao,
  fara,
}: {
  titulo: string;
  icone: LucideIcon;
  descricao: string;
  fara: string[];
}) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-16 pt-10">
      <Reveal>
        <div className="surface-card p-6 sm:p-8">
          <div className="flex items-center gap-3">
            <span className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary ring-1 ring-primary/25">
              <Icone className="size-6" />
            </span>
            <span className="rounded-full border border-border bg-surface-2/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Em construção
            </span>
          </div>

          <h1 className="mt-5 font-display text-2xl font-bold sm:text-3xl">{titulo}</h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{descricao}</p>

          <div className="mt-6 rounded-2xl bg-surface-2/50 p-5">
            <p className="text-sm font-semibold">O que esta seção vai fazer</p>
            <ul className="mt-3 space-y-2">
              {fara.map((item, i) => (
                <li key={i} className="flex gap-2.5 text-sm leading-relaxed text-muted-foreground">
                  <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <Link
            href="/turma"
            className="focus-nice mt-7 inline-flex items-center gap-2 rounded-full border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors duration-300 hover:border-primary/40 hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> Voltar ao painel
          </Link>
        </div>
      </Reveal>
    </div>
  );
}
