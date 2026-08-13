# NERV AI — Entrega do Marco: Mês 3

> **Marco:** Mês 3 — Implementação do sistema de interação com a IA
> **Status:** Entregável concluído · demonstração pendente de credencial do provedor de IA
> **Projeto:** NERV AI — Sistema de Inteligência Educacional Adaptativa (alinhado à BNCC)
> **Data:** 13/08/2026

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
| Aplicação web | `https://nerv-ai-sandy.vercel.app` | ✅ no ar |
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
| 6 | Resposta do modelo | provedor de IA | ⏳ pendente de credencial válida |

### 2.3 Transcrição da conversa

> **Pendente.** Esta seção será preenchida com a transcrição literal de perguntas
> e respostas assim que a credencial do provedor de IA estiver ativa (ver
> seção 3.2). O código, o ambiente e a cadeia de requisições já estão prontos e
> verificados: falta apenas a chave de acesso ao modelo.

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

### 3.2 Recebimento de respostas — pendência declarada

O modelo ainda não responde porque o provedor de IA rejeita a credencial
configurada:

```
400 INVALID_ARGUMENT — "Please pass a valid API key"
```

O erro é do provedor, não da aplicação: a requisição sai do servidor, chega ao
provedor e é recusada na autenticação. **Resolve-se substituindo o valor de
`AI_API_KEY` por uma chave válida** — não há alteração de código pendente.

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
| **Evidência** — demonstração do chat respondendo | ⏳ ambiente pronto; transcrição pendente de credencial |
| **Critério** — perguntas enviadas e respostas coerentes | ⏳ envio verificado; resposta pendente de credencial |

---

*Documento de evidência do Marco Mês 3 — NERV AI.*
