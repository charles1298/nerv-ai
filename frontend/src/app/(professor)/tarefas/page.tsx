"use client";

import { ClipboardList } from "lucide-react";
import { EmBreve } from "@/components/nerv/EmBreve";

export default function TarefasPage() {
  return (
    <EmBreve
      titulo="Tarefas"
      icone={ClipboardList}
      descricao="Ainda não está no ar. Nenhum dado desta tela é real — preferimos deixar vazio a mostrar entregas que não existem."
      fara={[
        "Criar listas de exercícios e enviá-las para uma turma inteira ou para alunos específicos.",
        "Acompanhar quem entregou, quem começou e quem nem abriu, com prazo por tarefa.",
        "Correção automática das questões de múltipla escolha, com o resultado já no painel.",
        "Alimentar a tutoria: o NERV prioriza na conversa os tópicos que você cobrou na tarefa.",
      ]}
    />
  );
}
