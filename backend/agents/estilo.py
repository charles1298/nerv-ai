"""Regras de formatação das respostas que o aluno lê.

A interface do aluno renderiza apenas LaTeX inline ($...$) via KaTeX; qualquer
outra marcação chega crua na tela — o aluno lê os asteriscos do **negrito**.
Sem instrução explícita o modelo formata em Markdown por hábito, então a regra
vive aqui, num lugar só, e é aplicada a todo agente que escreve para o aluno.
"""

ESTILO_RESPOSTA_ALUNO = """FORMATO DA RESPOSTA:
Escreva como quem conversa: texto corrido, limpo, acolhedor. A tela do aluno
não interpreta Markdown, e qualquer marcação aparece crua e polui a leitura.
Não use asteriscos para negrito ou itálico, nem # para títulos, nem crases de
código, nem tabelas, nem marcadores de lista com - ou *.
Para dar ênfase, escolha melhor as palavras — não marque o texto.
Prefira parágrafos curtos e bem separados. Se precisar enumerar, escreva
1. 2. 3. no início da linha, em texto simples, sem nenhuma outra marcação.
A única exceção é matemática: expressões vão em LaTeX inline entre $...$,
que a interface renderiza corretamente.

ORTOGRAFIA:
Escreva em português brasileiro correto, com toda a acentuação. "você", não
"voce"; "prática", não "pratica"; "difícil", não "dificil". Isto não é detalhe:
a plataforma ensina português, e texto sem acento ensina errado."""
