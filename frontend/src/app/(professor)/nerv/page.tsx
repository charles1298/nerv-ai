"use client";

import { Sparkles } from "lucide-react";
import { EmBreve } from "@/components/nerv/EmBreve";

export default function NervProfessorPage() {
  return (
    <EmBreve
      titulo="NERV para o professor"
      icone={Sparkles}
      descricao="Ainda não está no ar. O assistente do aluno já funciona; esta é a versão dele voltada para o seu trabalho."
      fara={[
        "Pedir em linguagem natural: 'monte uma lista de 10 questões de porcentagem para o 9º ano'.",
        "Perguntar sobre a própria turma: 'quem está travando em frações?' — usando os dados reais do painel.",
        "Gerar plano de aula a partir dos tópicos em que a turma foi pior.",
        "Rascunhar o recado para a família de um aluno em situação crítica.",
      ]}
    />
  );
}
