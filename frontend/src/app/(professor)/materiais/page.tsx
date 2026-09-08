"use client";

import { BookMarked } from "lucide-react";
import { EmBreve } from "@/components/nerv/EmBreve";

export default function MateriaisPage() {
  return (
    <EmBreve
      titulo="Materiais"
      icone={BookMarked}
      descricao="Ainda não está no ar. Nenhum dado desta tela é real — preferimos deixar vazio a mostrar uma biblioteca que não existe."
      fara={[
        "Subir PDFs, slides e listas para ficarem disponíveis aos alunos da turma.",
        "Indexar esse material no RAG, para o NERV responder com base no que VOCÊ ensinou.",
        "Marcar tópicos obrigatórios do bimestre, que a tutoria passa a priorizar.",
        "Ver quais materiais os alunos realmente abriram.",
      ]}
    />
  );
}
