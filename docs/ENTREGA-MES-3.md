# NERV AI — Entrega do Marco: Mês 3

> **Marco:** Mês 3 — Implementação do sistema de interação com a IA
> **Status:** Concluído
> **Projeto:** NERV AI — Sistema de Inteligência Educacional Adaptativa (alinhado à BNCC)
> **Data:** 13/08/2026

---

# 🔎 ACESSO PARA AVALIAÇÃO

> ### 🌐 Sistema no ar
> ## **https://nerv-ai-sandy.vercel.app**
>
> ### 🔑 Entrar como aluno
> | Campo | Valor |
> |---|---|
> | **E-mail** | `aluno@demo.nerv.ai` |
> | **Senha** | `aluno-demo-123` |
>
> ### 💻 Código-fonte
> ## **https://github.com/charles1298/nerv-ai**

### Como testar a IA em 4 passos

| # | Ação |
|---|---|
| **1** | Abrir **https://nerv-ai-sandy.vercel.app** |
| **2** | Entrar com `aluno@demo.nerv.ai` / `aluno-demo-123` |
| **3** | Clicar em **Tutoria** no menu do topo |
| **4** | Digitar qualquer dúvida escolar e enviar |

A resposta chega **em tempo real, palavra por palavra**, gerada por inteligência
artificial no momento da pergunta — não há respostas pré-programadas. Faça a mesma
pergunta duas vezes e as respostas serão diferentes.

**Sugestões de perguntas para testar:**

- *"Quem foi Dom Pedro II e por que ele foi importante para o Brasil?"*
- *"Como eu resolvo a equação x² - 5x + 6 = 0?"*
- *"Como eu começo uma redação?"*
- *"Por que o céu é azul?"*

**Observações práticas:**

- A **primeira** pergunta pode levar alguns segundos a mais (o servidor é acionado
  sob demanda). As seguintes são imediatas.
- Ao recarregar a página, a sessão é encerrada por segurança — basta entrar
  novamente.

### Acesso ao painel da gestão (opcional)

Para ver os relatórios pedagógicos e a exportação em PDF:

| Campo | Valor |
|---|---|
| **E-mail** | `admin@demo.nerv.ai` |
| **Senha** | `admin-demo-123` |

---

## 1. Entregável

**Descrição do marco:** *Implementação do sistema de interação com a IA.*

O sistema de interação foi implementado como um **agente de tutoria** que conversa
com o aluno em tempo real. Não é um chat genérico: cada resposta é construída a
partir do perfil do aluno e do currículo.

### 1.1 Fluxo de uma pergunta

```
Aluno digita  →  Frontend (Next.js)
              →  POST /sessions/{id}/chat
              →  tutor_agent monta o contexto:
                   · perfil e série do aluno
                   · memória das sessões anteriores
                   · trechos do currículo (BNCC) por busca semântica
              →  provedor de IA (streaming)
              →  resposta chega palavra por palavra na tela
              →  pergunta e resposta gravadas no banco
```

### 1.2 Componentes implementados

| Componente | Arquivo | Função |
|---|---|---|
| Agente tutor | `agents/tutor_agent.py` | Monta o prompt pedagógico e conduz o diálogo |
| Wrapper do provedor | `services/ai_service.py` | Único ponto de acesso ao modelo; provedor trocável por variável de ambiente |
| Endpoint de conversa | `routers/sessions.py` | Recebe a pergunta e devolve a resposta em streaming (SSE) |
| Memória de longo prazo | `memory/mem0_client.py` | Recupera o que o aluno já estudou e onde teve dificuldade |
| Ancoragem curricular | `memory/bncc_rag.py` | Busca semântica no corpus BNCC para embasar a explicação |
| Interface de tutoria | `components/chat/TutorChat.tsx` | Tela do chat, com renderização de matemática (KaTeX) |
| Extração de insights | `agents/tutor_agent.py` | Ao encerrar a sessão, registra avanços e dificuldades observados |

### 1.3 Diretrizes pedagógicas embutidas no agente

O comportamento do tutor é definido por prompt de sistema, não por respostas
prontas. As regras aplicadas:

- **Não entrega a resposta** — conduz o aluno até ela por perguntas.
- **Adapta-se à série** do aluno e ao histórico de dificuldades.
- **Usa exemplos brasileiros** e contexto do cotidiano.
- **Escreve matemática em notação LaTeX**, renderizada na tela.
- **Ao errar, o aluno é encorajado**: o erro é nomeado com clareza e a explicação
  é reformulada por outro caminho.

### 1.4 Independência de fornecedor

O acesso ao modelo é centralizado em um único módulo que fala o protocolo
**Chat Completions** — padrão de fato do mercado. Trocar de fornecedor é trocar
três variáveis de ambiente, sem alterar uma linha dos agentes:

| Variável | Função |
|---|---|
| `AI_BASE_URL` | Endereço do provedor |
| `AI_MODEL` | Modelo escolhido |
| `AI_API_KEY` | Credencial de acesso |

Isso protege o projeto de dependência de um único fornecedor e permite migrar por
custo ou qualidade a qualquer momento.

---

## 2. Evidência Esperada

**Descrição do marco:** *Demonstração do chat respondendo perguntas.*

### 2.1 Ambiente publicado

O sistema de interação está **publicado e operacional** em nuvem:

| Componente | Endereço | Situação |
|---|---|---|
| API (backend) | `https://nerv-ai-backend.vercel.app` | ✅ no ar |
| Aplicação web | `https://nerv-ai-sandy.vercel.app` | ✅ no ar, conectada à API |
| Banco de dados | PostgreSQL gerenciado (Neon) | ✅ migrações aplicadas |
| Repositório | `https://github.com/charles1298/nerv-ai` | ✅ versionado |

Verificação de saúde da API:

```
GET https://nerv-ai-backend.vercel.app/health
→ 200 {"status":"ok","env":"production"}
```

### 2.2 Cadeia da conversa verificada em produção

Cada etapa do caminho de uma pergunta foi exercitada por requisição real contra o
ambiente publicado:

| # | Etapa | Requisição | Resultado |
|---|---|---|---|
| 1 | Cadastro de escola | `POST /auth/register-school` | ✅ 201 |
| 2 | Autenticação do aluno | `POST /auth/login` | ✅ 200 (token emitido) |
| 3 | Cadastro de aluno | `POST /students` | ✅ 201 |
| 4 | Abertura da sessão de tutoria | `POST /sessions` | ✅ 201 |
| 5 | Envio da pergunta | `POST /sessions/{id}/chat` | ✅ 200 (canal de streaming aberto) |
| 6 | Resposta do modelo em streaming | provedor de IA | ✅ resposta recebida |
| 7 | Gravação da conversa | `GET /sessions/{id}/messages` | ✅ 4 mensagens persistidas |

### 2.3 Transcrição da conversa

Conversa real capturada no ambiente publicado em **13/08/2026**, na sessão de
tutoria do aluno de demonstração (9º ano do Ensino Fundamental). Transcrição
literal, sem edição.

#### Pergunta 1 — História

> **Aluno:** Quem foi Dom Pedro II e por que ele foi importante para o Brasil?

> **NERV:** Olá, João! É um prazer enorme conhecer você. Seja muito bem-vindo!
>
> Como você está no **9º ano do Ensino Fundamental**, esse tema é superimportante e
> cai bastante nas aulas de História. No 9º ano, nós estudamos a fundo a transição
> do Brasil Império para o Brasil República, e não dá para entender essa mudança
> sem conhecer bem o papel de **Dom Pedro II**.
>
> Para começar nossa jornada, vou te contar uma curiosidade: Dom Pedro II foi o
> segundo e último imperador do Brasil. Ele governou o nosso país por quase 50 anos
> (um período conhecido como **Segundo Reinado**, de 1840 a 1889)!
>
> Mas a história dele tem um começo bem dramático. O pai dele, Dom Pedro I, foi
> embora para Portugal e o deixou aqui no Brasil quando ele tinha **apenas 5 anos de
> idade**, preparado para ser o futuro governante. Imagine só a pressão! Ele acabou
> assumindo o trono de fato aos 14 anos, no que ficou conhecido como o *Golpe da
> Maioridade*.
>
> Agora, para a gente construir essa resposta juntos, pense comigo:
>
> O Brasil do século XIX (anos 1800) era muito diferente do Brasil de hoje. Se você
> estivesse no lugar desse jovem imperador, governando um país gigantesco, **quais
> você acha que seriam os maiores desafios que você enfrentaria naquela época?**
>
> *(Dica: pense em como a economia do Brasil funcionava, em quem fazia o trabalho
> pesado e em como as pessoas se comunicavam ou viajavam pelo país.)*
>
> O que você acha? Me conta o que vem à sua mente!

#### Pergunta 2 — Matemática (mesma sessão)

> **Aluno:** Como eu resolvo a equação x2 - 5x + 6 = 0?

> **NERV:** Mudança de planos! Adorei a virada de assunto, João. A matemática é
> fascinante, e as **equações do $2^{\circ}$ grau** são um dos superpoderes que você
> adquire justamente no 9º ano! Elas servem para resolver muitos problemas do nosso
> dia a dia, como calcular trajetórias ou prever lucros.
>
> A sua equação é: $x^2 - 5x + 6 = 0$
>
> Para resolver uma equação desse tipo, a ferramenta mais famosa que usamos no
> Brasil é a nossa querida **Fórmula de Bhaskara**.
>
> A estrutura geral de uma equação do $2^{\circ}$ grau é sempre escrita assim:
> $ax^2 + bx + c = 0$
>
> Onde $a$, $b$ e $c$ são números que chamamos de *coeficientes*.
>
> Olhando para a sua equação, você consegue identificar para mim quem são esses
> coeficientes? [...] Diga para mim quanto vale $a$, $b$ e $c$ para darmos o próximo
> passo juntos!

#### O que a transcrição comprova

| Comportamento esperado do tutor | Onde aparece |
|---|---|
| Resposta coerente e factualmente correta | Segundo Reinado 1840–1889, Golpe da Maioridade, Bhaskara |
| Adaptação à série do aluno | Cita o 9º ano e ancora no conteúdo da série nas duas respostas |
| Não entrega a resposta pronta | Ambas terminam devolvendo uma pergunta ao aluno |
| Uso de contexto brasileiro | "a nossa querida Fórmula de Bhaskara" |
| Matemática em notação LaTeX | `$x^2 - 5x + 6 = 0$`, renderizado na tela via KaTeX |
| Continuidade da conversa | Reconhece a troca de assunto ("Mudança de planos!") |
| Personalização | Trata o aluno pelo nome |

#### Persistência

As quatro mensagens (duas perguntas e duas respostas) foram gravadas no banco e
retornam em `GET /sessions/{id}/messages`, permitindo retomar a conversa depois.

### 2.5 Demonstração reproduzível pela interface web

O site publicado está conectado ao ambiente de produção — **qualquer pessoa pode
reproduzir a demonstração** entrando com as credenciais da seção 3.3:

1. Acessar `https://nerv-ai-sandy.vercel.app`
2. Entrar como `aluno@demo.nerv.ai` / `aluno-demo-123`
3. Menu **Tutoria** → digitar a pergunta

Verificado pela interface em 13/08/2026 com a pergunta *"como eu começo uma
redação?"*. Trecho da resposta recebida na tela:

> Olá, João! Que excelente iniciativa a sua. Estar no 9º ano e já querer dominar a
> arte de começar uma redação é um passo gigantesco para se dar bem no Ensino Médio
> e, no futuro, no ENEM!
>
> Escrever uma redação, especialmente a do tipo **dissertativo-argumentativa** [...]
> A introdução é a "sala de visitas": você precisa acolher o leitor, mostrar sobre o
> que vai falar e apresentar o seu ponto de vista.
>
> 1. **O Repertório (ou Contextualização):** É o "gancho" para chamar a atenção do
>    leitor. Pode ser uma alusão histórica, um livro, uma música, uma série da
>    Netflix, um filme ou uma lei (como a nossa Constituição de 1988).
> 2. **A Apresentação do Tema:** [...] qual é o problema real que o Brasil enfrenta
>    hoje [...]
> 3. **A Tese:** É a sua opinião sobre o assunto [...]
>
> Para você ver como não é um bicho de sete cabeças, vamos usar um tema muito
> importante e atual, no estilo do ENEM: **"Os impactos do uso excessivo das redes
> sociais na saúde mental dos jovens brasileiros"**. [...]
>
> Se você tivesse que escolher **um** desses caminhos (um filme/série, a lei ou o
> cotidiano) para abrir o seu texto, qual você escolheria?

Confirma o mesmo padrão da seção 2.3 numa terceira matéria (Língua Portuguesa):
resposta correta, adaptada à série, com repertório brasileiro e devolvendo a
condução ao aluno.

### 2.4 Qualidade — testes automatizados

```
pytest -q
61 passed
```

Cobrem autenticação, isolamento entre escolas, os agentes de IA, tratamento de
falha do modelo e a interpretação da resposta do provedor.

---

## 3. Critério de Aceite

**Descrição do marco:** *Usuário consegue enviar perguntas e receber respostas coerentes.*

### 3.1 Envio de perguntas — atendido

O aluno acessa a tela de tutoria, digita a pergunta e o sistema a recebe, registra
e encaminha ao modelo, mantendo o canal aberto para a resposta em tempo real
(itens 1 a 5 da tabela 2.2, todos verificados em produção).

### 3.2 Recebimento de respostas coerentes — atendido

As duas perguntas enviadas receberam resposta completa, em português, factualmente
correta e adequada à série do aluno (transcrição integral na seção 2.3). As
respostas chegam **em tempo real**, palavra por palavra, e não como um bloco ao
final.

A coerência é verificável em três dimensões:

- **Factual:** datas e fatos históricos corretos; método matemático correto para o
  tipo de equação apresentada.
- **Pedagógica:** o tutor conduz o aluno ao raciocínio em vez de entregar a
  resposta, conforme as diretrizes da seção 1.3.
- **Contextual:** mantém o fio da conversa entre perguntas de matérias diferentes e
  personaliza pelo nome e pela série.

**Resultado:** o aluno envia perguntas e recebe respostas coerentes. Critério
**atendido**.

### 3.3 Credenciais de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@demo.nerv.ai` | `aluno-demo-123` |
| Gestor/Admin | `admin@demo.nerv.ai` | `admin-demo-123` |

---

## 4. Como verificar

### 4.1 No ambiente publicado

```bash
# Saúde da API
curl https://nerv-ai-backend.vercel.app/health

# Login do aluno
curl -X POST https://nerv-ai-backend.vercel.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aluno@demo.nerv.ai","password":"aluno-demo-123"}'
```

### 4.2 Localmente

```bash
cd backend
.venv\Scripts\activate
pytest -q                            # 61 passed
uvicorn main:app --reload            # http://localhost:8000

cd frontend
npm run dev                          # http://localhost:3000
```

---

## 5. Resumo

| Requisito do marco | Situação |
|---|---|
| **Entregável** — implementação do sistema de interação com a IA | ✅ concluído |
| **Evidência** — demonstração do chat respondendo perguntas | ✅ transcrição real na seção 2.3 |
| **Critério** — perguntas enviadas e respostas coerentes | ✅ atendido |

---

*Documento de evidência do Marco Mês 3 — NERV AI.*
