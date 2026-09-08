"use client";

import { HelpCircle } from "lucide-react";
import { EmBreve } from "@/components/nerv/EmBreve";

export default function DuvidasPage() {
  return (
    <EmBreve
      titulo="Dúvidas"
      icone={HelpCircle}
      descricao="Ainda não está no ar. Nenhum dado desta tela é real — preferimos deixar vazio a inventar perguntas de aluno."
      fara={[
        "Agrupar as dúvidas mais frequentes das suas turmas por tópico, vindas das conversas com o NERV.",
        "Mostrar onde a turma inteira travou, para você retomar aquilo na próxima aula.",
        "Sinalizar dúvida recorrente de um aluno específico, antes que ele desista da matéria.",
        "Respeitando a LGPD: agregados e temas, sem expor a conversa individual do aluno.",
      ]}
    />
  );
}
