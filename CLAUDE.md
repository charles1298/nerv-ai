# NERV AI — Sistema de Inteligência Educacional Adaptativa
### `CLAUDE.md` — Especificação Master para Claude Fable 5

> **Modelo-alvo:** Claude Fable 5 (claude-fable-5)
> **Stack:** Python 3.12 · FastAPI · React 19 · TypeScript · PostgreSQL · Redis · Mem0 · Claude API
> **Contexto:** Plataforma SaaS multi-tenant de tutoria adaptativa para escolas públicas e privadas do Brasil, alinhada à BNCC.

---

## 0. MISSÃO DO PROJETO

Construir uma plataforma completa de IA educacional capaz de:

- **Tutoria 1-on-1 infinita** para cada aluno, adaptada ao nível, ritmo e estilo de aprendizagem individual.
- **Geração automática de conteúdo** — exercícios, questões ENEM/vestibulares, redações, mapas mentais — todos alinhados com a BNCC.
- **Análise profunda de desempenho** com relatórios para alunos, professores e gestores escolares.
- **Suporte multimodal real** — o aluno fotografa a prova ou o caderno, e a IA analisa, corrige e ensina na hora.
- **Memória persistente de longo prazo** por aluno, para que o tutor realmente "lembre" de onde parou e o que o aluno ainda não entendeu.

Este projeto existe para democratizar acesso a tutoria de qualidade em todo o Brasil. Cada aluno merece um tutor infinitamente paciente, especializado em todas as matérias, disponível 24h.

---

## 1. ESTRUTURA DO REPOSITÓRIO

```
nerv-ai/
├── backend/
│   ├── main.py                  # Entrypoint FastAPI
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy async engine
│   │   └── security.py          # JWT, bcrypt, rate limiting
│   ├── agents/
│   │   ├── tutor_agent.py       # Agente principal de tutoria (Fable 5)
│   │   ├── exercise_agent.py    # Geração adaptativa de exercícios
│   │   ├── redacao_agent.py     # Avaliação e feedback de redações
│   │   ├── vision_agent.py      # Análise de fotos de provas/cadernos
│   │   └── report_agent.py      # Geração de relatórios pedagógicos
│   ├── memory/
│   │   ├── mem0_client.py       # Integração Mem0 por aluno
│   │   ├── bncc_rag.py          # RAG sobre corpus BNCC + materiais
│   │   └── student_profile.py   # Perfil adaptativo persistente
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic v2 schemas
│   ├── routers/                 # FastAPI routers por domínio
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── sessions.py          # Sessões de tutoria
│   │   ├── exercises.py
│   │   ├── upload.py            # Upload multimodal (foto/PDF)
│   │   └── reports.py
│   └── services/
│       ├── anthropic_service.py # Wrapper do Claude Fable 5
│       ├── storage_service.py   # S3-compatible (Cloudflare R2)
│       └── notification_service.py
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 14 App Router
│   │   │   ├── (aluno)/         # Layout do aluno
│   │   │   ├── (professor)/     # Layout do professor
│   │   │   ├── (gestor)/        # Layout do gestor/diretor
│   │   │   └── (auth)/
│   │   ├── components/
│   │   │   ├── chat/            # Interface de tutoria
│   │   │   │   ├── TutorChat.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── MathRenderer.tsx  # KaTeX inline
│   │   │   │   └── ImageUpload.tsx
│   │   │   ├── exercises/
│   │   │   ├── dashboard/
│   │   │   └── ui/              # shadcn/ui components
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── store/               # Zustand global state
│   └── public/
│
├── infra/
│   ├── docker-compose.yml       # Dev local completo
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── railway.toml             # Deploy Railway
│
├── scripts/
│   ├── seed_bncc.py             # Indexa corpus BNCC no vector DB
│   ├── seed_enem.py             # Indexa banco de questões ENEM
│   └── test_agents.py           # Suite de testes dos agentes
│
└── CLAUDE.md                    # Este arquivo
```

---

## 2. STACK TÉCNICA COMPLETA

### Backend
| Camada | Tecnologia | Versão |
|---|---|---|
| Runtime | Python | 3.12 |
| Framework | FastAPI | 0.115.x |
| ORM | SQLAlchemy (async) | 2.0 |
| Migrations | Alembic | latest |
| Validação | Pydantic v2 | 2.x |
| Auth | python-jose + bcrypt | — |
| Cache/Queue | Redis (Upstash) | — |
| WebSocket | FastAPI + websockets | — |
| Vector DB | pgvector (PostgreSQL) | — |
| Object Storage | Cloudflare R2 (boto3) | — |

### AI Stack
| Componente | Tecnologia | Uso |
|---|---|---|
| LLM principal | Claude Fable 5 | Tutoria, geração, análise |
| Memória | Mem0 (cloud) | Perfil persistente por aluno |
| RAG | pgvector + LlamaIndex | Corpus BNCC, ENEM |
| Visão | Claude Fable 5 (vision) | Análise de fotos de provas |
| Embeddings | claude-fable-5 embeddings | Busca semântica |

### Frontend
| Camada | Tecnologia |
|---|---|
| Framework | Next.js 14 (App Router) |
| UI | shadcn/ui + Tailwind CSS |
| Estado | Zustand |
| Formulários | React Hook Form + Zod |
| Gráficos | Recharts |
| Matemática | KaTeX |
| Streaming | Vercel AI SDK |
| Animações | Framer Motion |

### Infra
| Componente | Provedor |
|---|---|
| Backend | Railway (auto-deploy) |
| Frontend | Vercel |
| DB | Railway PostgreSQL |
| Cache | Upstash Redis |
| Storage | Cloudflare R2 |
| CDN | Cloudflare |

---

## 3. REGRAS DE DESENVOLVIMENTO (CRÍTICO — LEIA ANTES DE QUALQUER CÓDIGO)

### 3.1 Princípios Gerais

- **Fable 5 is the executor.** Você é o agente principal. Planeje a tarefa completa antes de começar a codar. Use seu raciocínio de longo contexto para manter consistência em todo o codebase.
- **Sem código placeholder.** Cada função entregue deve ser funcional e testável. `# TODO` e `pass` são proibidos em código de produção.
- **TypeScript strict mode.** Sem `any`. Todos os tipos explicitamente definidos.
- **Python type hints completos.** Todas as funções com assinatura tipada.
- **Tratamento de erro em toda chamada à API.** Falhas da Claude API, Mem0 e banco de dados devem ser tratadas explicitamente com logs estruturados.

### 3.2 Padrão de Chamada do Claude Fable 5

```python
# backend/services/anthropic_service.py
# Sempre usar este padrão. NUNCA instanciar Anthropic() diretamente em outros arquivos.

import anthropic
from typing import AsyncGenerator
import structlog

logger = structlog.get_logger()

client = anthropic.Anthropic()

FABLE_5_MODEL = "claude-fable-5"

async def stream_tutor_response(
    system_prompt: str,
    messages: list[dict],
    student_id: str,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """
    Stream de resposta do Fable 5 para a sessão de tutoria.
    Usa extended thinking para problemas complexos (matemática, redação).
    """
    try:
        with client.messages.stream(
            model=FABLE_5_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.APIError as e:
        logger.error("anthropic_api_error", student_id=student_id, error=str(e))
        raise
```

### 3.3 Padrão de Memória (Mem0)

```python
# backend/memory/mem0_client.py
# Toda memória de aluno é armazenada e recuperada via Mem0 com o student_id como user_id.

from mem0 import MemoryClient
import os

mem0 = MemoryClient(api_key=os.environ["MEM0_API_KEY"])

async def get_student_context(student_id: str, query: str) -> str:
    """
    Recupera memórias relevantes do aluno para enriquecer o system prompt.
    Retorna string formatada para ser injetada no prompt.
    """
    memories = mem0.search(query=query, user_id=student_id, limit=10)
    if not memories:
        return "Primeira interação com este aluno. Sem histórico."
    
    context_lines = [f"- {m['memory']}" for m in memories]
    return "Contexto do aluno (memórias anteriores):\n" + "\n".join(context_lines)

async def save_session_insights(
    student_id: str,
    insights: list[str],
) -> None:
    """
    Salva insights da sessão — dificuldades, avanços, conceitos aprendidos.
    Chamado ao final de cada sessão de tutoria.
    """
    for insight in insights:
        mem0.add(
            messages=[{"role": "user", "content": insight}],
            user_id=student_id,
        )
```

### 3.4 Naming Conventions

- **Backend:** snake_case em Python, PEP8 estrito.
- **Frontend:** camelCase em TypeScript, PascalCase em componentes React.
- **Banco de dados:** snake_case em todas as tabelas e colunas.
- **Variáveis de ambiente:** SCREAMING_SNAKE_CASE, prefixadas por domínio: `ANTHROPIC_API_KEY`, `MEM0_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `R2_BUCKET_NAME`.
- **IDs:** UUIDs v4 em todas as entidades.

---

## 4. ESQUEMA DO BANCO DE DADOS

```sql
-- Hierarquia: Escola → Turma → Aluno
-- Multi-tenant: escola_id em todas as tabelas relevantes

-- Escolas (tenants)
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    plan VARCHAR(20) DEFAULT 'free', -- free | basic | pro | enterprise
    max_students INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usuários unificados (aluno, professor, gestor, admin)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL, -- student | teacher | manager | admin
    grade VARCHAR(20),         -- 1ano_ef | ... | 3ano_em (para alunos)
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Matérias e tópicos (alinhados BNCC)
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,        -- "Matemática", "Língua Portuguesa"
    bncc_code VARCHAR(20),             -- Ex: MT, LP, CN, CH
    grade_range VARCHAR(20)            -- EF1, EF2, EM
);

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id),
    name VARCHAR(200) NOT NULL,
    bncc_skill_code VARCHAR(30),       -- Ex: EF09MA07
    description TEXT,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5)
);

-- Sessões de tutoria
CREATE TABLE tutoring_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id),
    subject_id UUID REFERENCES subjects(id),
    topic_id UUID REFERENCES topics(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    messages_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    quality_score FLOAT,               -- Avaliado pelo modelo ao final da sessão
    insights JSONB DEFAULT '[]'        -- Insights para Mem0
);

-- Mensagens das sessões
CREATE TABLE session_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES tutoring_sessions(id),
    role VARCHAR(10) NOT NULL,         -- user | assistant
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text', -- text | image | math | code
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exercícios gerados
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id),
    topic_id UUID REFERENCES topics(id),
    content JSONB NOT NULL,            -- {question, options, answer, explanation, tipo}
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    tipo VARCHAR(30),                  -- multipla_escolha | dissertativa | redacao | calculo
    source VARCHAR(20) DEFAULT 'ai',   -- ai | enem | vestibular
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tentativas de exercícios
CREATE TABLE exercise_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID REFERENCES exercises(id),
    student_id UUID REFERENCES users(id),
    answer TEXT,
    is_correct BOOLEAN,
    score FLOAT,                       -- 0.0 - 10.0
    feedback TEXT,                     -- Feedback detalhado do Fable 5
    time_spent_seconds INTEGER,
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploads multimodais
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id),
    session_id UUID REFERENCES tutoring_sessions(id),
    filename TEXT NOT NULL,
    r2_key TEXT NOT NULL,
    mime_type VARCHAR(50),
    analysis_result JSONB,             -- Resultado da análise por visão do Fable 5
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Desempenho agregado (materializado diariamente)
CREATE TABLE student_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id),
    subject_id UUID REFERENCES subjects(id),
    period_date DATE NOT NULL,
    sessions_count INTEGER DEFAULT 0,
    exercises_attempted INTEGER DEFAULT 0,
    exercises_correct INTEGER DEFAULT 0,
    avg_score FLOAT,
    mastered_topics TEXT[],
    struggling_topics TEXT[],
    UNIQUE (student_id, subject_id, period_date)
);

-- pgvector para RAG (corpus BNCC + questões ENEM)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id),
    topic_id UUID REFERENCES topics(id),
    content TEXT NOT NULL,
    source VARCHAR(50),                -- bncc | enem | livro_didatico
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 5. AGENTES DE IA

### 5.1 Agente Tutor Principal (`tutor_agent.py`)

**Função:** Conduzir sessões de tutoria adaptativa 1-on-1 com cada aluno.

**Comportamento esperado:**
- Recuperar memórias do aluno via Mem0 antes de cada sessão.
- Identificar o nível de compreensão do aluno ao longo da conversa (adaptação contínua).
- Usar exemplos do cotidiano brasileiro (regiões, culturas, referências locais).
- Para matemática: usar notação LaTeX inline (`$...$`) para todas as expressões.
- Para ciências: citar experimentos simples que o aluno pode fazer em casa.
- Para português: praticar redação com temas reais do ENEM recente.
- Ao final de cada sessão, gerar uma lista de `insights` para salvar no Mem0:
  - Tópicos dominados nesta sessão.
  - Dificuldades identificadas.
  - Estilo de aprendizagem observado (visual, auditivo, prático).
  - Próximos tópicos recomendados.

**System prompt base:**
```
Você é NERV, tutor de IA educacional para estudantes brasileiros do Ensino Fundamental e Médio.
Você tem acesso ao histórico completo deste aluno e deve usá-lo para personalizar cada resposta.
Você é paciente, encorajador e nunca dá a resposta diretamente — você guia o aluno a descobrir.
Quando o aluno errar, elogie o esforço, identifique o erro com clareza e reformule a explicação.
Você conhece profundamente a BNCC e alinha cada explicação às competências e habilidades exigidas.
Mantenha um equilíbrio entre rigor acadêmico e linguagem acessível para a faixa etária do aluno.
Use exemplos brasileiros sempre que possível.

CONTEXTO DO ALUNO:
{student_context}

PERFIL:
Nome: {student_name}
Série: {grade}
Matéria: {subject}
Tópico desta sessão: {topic}
```

### 5.2 Agente de Exercícios (`exercise_agent.py`)

**Função:** Gerar exercícios adaptativos baseados no desempenho histórico do aluno.

**Comportamento esperado:**
- Analisar o histórico de tentativas do aluno no tópico.
- Gerar exercícios no nível N+1 (um pouco além do conforto atual).
- Variar os tipos: múltipla escolha, verdadeiro/falso, cálculo passo-a-passo, dissertativa.
- Para turmas de 3º EM: gerar questões no estilo ENEM (com texto motivador, 5 alternativas, nível progressivo).
- Retornar JSON estruturado validável por Pydantic.

**Schema de saída (JSON):**
```json
{
  "question": "Texto completo da questão",
  "tipo": "multipla_escolha | dissertativa | calculo | redacao",
  "difficulty": 3,
  "alternatives": [
    {"label": "A", "text": "...", "is_correct": false},
    {"label": "B", "text": "...", "is_correct": true},
    {"label": "C", "text": "...", "is_correct": false},
    {"label": "D", "text": "...", "is_correct": false},
    {"label": "E", "text": "...", "is_correct": false}
  ],
  "correct_answer": "B",
  "step_by_step_solution": "Passo 1: ...\nPasso 2: ...\nPortanto...",
  "bncc_skill": "EF09MA07",
  "hints": ["Pensa na fórmula de...", "Lembre que..."],
  "common_mistakes": ["Confundir X com Y", "Esquecer de..."]
}
```

### 5.3 Agente de Redação (`redacao_agent.py`)

**Função:** Avaliar redações completas no modelo ENEM com feedback detalhado.

**Critérios de avaliação (fiel ao ENEM):**
- **C1 — Domínio da norma culta** (0–200): gramática, ortografia, pontuação, concordância.
- **C2 — Compreensão do tema** (0–200): adequação ao tema proposto, repertório sociocultural.
- **C3 — Argumentação** (0–200): progressão argumentativa, coerência, coesão.
- **C4 — Mecanismos linguísticos** (0–200): conectivos, coesão referencial, progressão textual.
- **C5 — Proposta de intervenção** (0–200): proposta concreta, agentes, ações, finalidade.

**Output esperado:**
```json
{
  "nota_total": 760,
  "notas_por_criterio": {
    "C1": 160, "C2": 200, "C3": 160, "C4": 160, "C5": 80
  },
  "analise_detalhada": {
    "pontos_fortes": ["..."],
    "pontos_fracos": ["..."],
    "erros_gramaticais": [
      {"trecho": "...", "erro": "...", "correcao": "..."}
    ]
  },
  "reescrita_sugerida": "Trecho reescrito com melhorias...",
  "nota_estimada_real_enem": "Entre 640 e 720",
  "proximos_passos": ["Praticar proposta de intervenção", "Revisar conectivos adversativos"]
}
```

### 5.4 Agente de Visão (`vision_agent.py`)

**Função:** Analisar fotos de provas, cadernos, exercícios e materiais fotografados pelo aluno.

**Capacidades:**
- **OCR inteligente:** Extrair texto de fotos de caderno, mesmo com letra ruim.
- **Correção de prova:** Aluno fotografa prova corrigida → IA analisa cada erro e explica.
- **Resolução de exercício:** Aluno fotografa exercício do livro → IA resolve passo a passo.
- **Análise de gráficos:** Aluno fotografa gráfico/tabela → IA interpreta e ensina a ler.
- **Geometria:** Aluno fotografa figura geométrica desenhada → IA identifica e resolve.

**Implementação (usa vision do Fable 5):**
```python
async def analyze_uploaded_image(
    image_base64: str,
    mime_type: str,
    student_prompt: str,
    student_context: str,
) -> dict:
    """
    Analisa imagem enviada pelo aluno.
    student_prompt: O que o aluno quer saber sobre a imagem.
    """
    response = client.messages.create(
        model=FABLE_5_MODEL,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"""
Contexto do aluno: {student_context}

Pergunta do aluno: {student_prompt}

Analise esta imagem educacional. Identifique:
1. Tipo de conteúdo (exercício, prova, gráfico, diagrama, texto...)
2. Matéria e tópico
3. Responda à pergunta do aluno de forma didática
4. Se houver erros do aluno visíveis, explique com cuidado
5. Se for um exercício não resolvido, guie passo a passo (sem dar a resposta direta)
""",
                    },
                ],
            }
        ],
    )
    return {"analysis": response.content[0].text}
```

### 5.5 Agente de Relatórios (`report_agent.py`)

**Função:** Gerar relatórios pedagógicos completos para professores e gestores.

**Tipos de relatório:**
- **Relatório individual do aluno** (semanal/mensal): desempenho por tópico, evolução, recomendações.
- **Relatório de turma:** distribuição de performance, tópicos críticos, alunos em risco.
- **Relatório de escola:** comparativo por turma, análise de professores, eficácia por matéria.
- **Diagnóstico BNCC:** % de habilidades dominadas por turma/escola.

---

## 6. SISTEMA DE MEMÓRIA E PERSONALIZAÇÃO

### 6.1 Perfil Adaptativo do Aluno

Cada aluno tem um perfil dinâmico que evolui a cada sessão:

```python
# backend/memory/student_profile.py

STUDENT_PROFILE_TEMPLATE = {
    # Estilo de aprendizagem
    "learning_style": None,            # visual | auditivo | cinestésico | leitura
    "preferred_explanation_format": None,  # exemplos | fórmulas | histórias | exercícios
    
    # Desempenho por matéria
    "subject_performance": {
        "matematica": {"level": 3, "strong_topics": [], "weak_topics": []},
        "portugues": {"level": 3, "strong_topics": [], "weak_topics": []},
        # ...
    },
    
    # Padrões comportamentais
    "best_study_time": None,           # Inferido via timestamps
    "avg_session_duration_minutes": 0,
    "persistence_score": 0.0,          # Quantas vezes tenta antes de desistir
    "curiosity_topics": [],            # Temas que o aluno pergunta espontaneamente
    
    # ENEM prep (para 3º EM)
    "enem_target_score": None,
    "simulado_history": [],
    "redacao_evolution": [],
    
    # Motivacional
    "achievements": [],
    "streak_days": 0,
    "xp_total": 0,
}
```

### 6.2 RAG — Base de Conhecimento Educacional

**Corpus indexado no pgvector:**

| Fonte | Documentos | Descrição |
|---|---|---|
| BNCC completo | ~500 habilidades | Competências EF e EM |
| Banco ENEM | ~3.000 questões | 2009–2024 (domínio público) |
| Livros didáticos PNLD | Aprovados MEC | Conteúdo referência |
| Vestibulares BR | ~5.000 questões | FUVEST, UNICAMP, UFMG, UNB... |

**Uso no Tutor Agent:** Antes de cada resposta sobre um tópico específico, o agente faz busca semântica no corpus para grounding factual — garantindo que a explicação seja alinhada ao currículo oficial.

---

## 7. INTERFACE DO USUÁRIO (FRONTEND)

### 7.1 Interface do Aluno (`/aluno`)

**Visual:** Dark mode por padrão, cyberpunk educacional. Paleta: preto profundo `#0A0A0F` + roxo `#7C3AED` + verde neon `#39FF14` (destaques). Typography: `Space Grotesk` (display) + `Inter` (corpo). Referência estética: Eva.Tech / Evangelion, mas adaptada para contexto escolar.

**Telas principais:**
- **Home/Dashboard:** Streak, XP, próxima sessão recomendada, exercícios pendentes.
- **Chat de Tutoria:** Interface conversacional com streaming de respostas, renderização KaTeX para matemática, botão de upload de foto, indicador de "NERV está pensando...".
- **Exercícios:** Feed de exercícios do nível atual, timer, feedback imediato.
- **Redação:** Editor de texto com contagem de palavras, envio para correção, histórico de redações com evolução de notas.
- **Perfil & Conquistas:** Heatmap de estudo, badges, evolução histórica.

### 7.2 Interface do Professor (`/professor`)

**Telas:**
- **Dashboard da Turma:** Cards por aluno com status (em dia / atenção / crítico), ordenados por necessidade de intervenção.
- **Relatório Individual:** Timeline de progresso do aluno, tópicos dominados/fracos, transcrição de sessões (opcional).
- **Gestão de Conteúdo:** Professor cria listas de tópicos obrigatórios → NERV prioriza na tutoria.
- **Alertas:** NERV identifica alunos com dificuldade persistente → notifica professor automaticamente.

### 7.3 Interface do Gestor (`/gestor`)

**Telas:**
- **Visão da Escola:** Mapa de calor de desempenho por turma/matéria/tópico.
- **Comparativo BNCC:** % de habilidades dominadas vs. meta da escola.
- **Exportação:** Relatórios em PDF para reuniões pedagógicas.

---

## 8. SISTEMA DE GAMIFICAÇÃO

```python
# Regras de XP e conquistas

XP_RULES = {
    "sessao_completada": 50,
    "exercicio_correto_primeira_tentativa": 30,
    "exercicio_correto_segunda_tentativa": 15,
    "redacao_submetida": 40,
    "redacao_acima_de_800": 100,
    "streak_7_dias": 200,
    "streak_30_dias": 1000,
    "topico_dominado": 150,
    "modulo_completado": 500,
}

BADGES = [
    {"id": "primeira_sessao", "name": "Início de Jornada", "xp_reward": 50},
    {"id": "matematico", "name": "Mente Matemática", "condition": "10 exercícios de mat corretos"},
    {"id": "escritor", "name": "Redator ENEM", "condition": "nota 800+ em redação"},
    {"id": "estudioso", "name": "Dedicação Total", "condition": "30 dias de streak"},
    {"id": "explorador", "name": "Curioso Nato", "condition": "5 matérias diferentes em 1 semana"},
    {"id": "mestre_bncc", "name": "Mestre BNCC", "condition": "100% de habilidades EF dominadas"},
]
```

---

## 9. AUTENTICAÇÃO E MULTI-TENANT

### Fluxo de Auth

```
Escola cadastra → Admin cria professores → Professor cria alunos
                                         → Aluno recebe convite via e-mail/SMS
                                         → Aluno define senha → Token JWT (24h) + Refresh Token (30d)
```

### JWT Payload
```python
{
    "sub": "user_uuid",
    "school_id": "school_uuid",
    "role": "student | teacher | manager | admin",
    "grade": "3ano_em",            # apenas students
    "exp": timestamp
}
```

### Rate Limiting (Redis)
```python
RATE_LIMITS = {
    "tutoring_messages": "30/minute",    # por aluno
    "exercise_generation": "20/minute",  # por aluno
    "image_uploads": "10/minute",        # por aluno
    "redacao_submission": "5/hour",      # por aluno
}
```

---

## 10. PLANO DE DESENVOLVIMENTO (FASES)

### FASE 1 — MVP (Semanas 1–4)
**Objetivo:** Sistema funcional com tutoria básica e exercícios.

- [x] Setup do projeto (estrutura de pastas, Docker Compose, variáveis de ambiente)
- [x] Banco de dados e migrations (models MVP do item 4 + Alembic configurado; tabelas de Fase 2/3 — uploads, student_performance, knowledge_chunks — entram junto com seus módulos)
- [x] Auth completo (registro, login, JWT, refresh)
- [x] `tutor_agent.py` básico (sem memória) com streaming
- [x] Interface de chat do aluno (Next.js + SSE)
- [x] `exercise_agent.py` básico (múltipla escolha, dificuldade adaptativa N+1)
- [x] CRUD de exercícios e tentativas (correção local de múltipla escolha)
- [ ] Deploy no Railway (backend) + Vercel (frontend) — requer contas/credenciais do time

**Critério de aceite do MVP:** Um aluno consegue fazer login, conversar com o tutor sobre um tópico de matemática, e responder exercícios gerados por IA.

### FASE 2 — Plataforma Completa (Semanas 5–10)
**Objetivo:** Memória, visão, redação, gamificação e interface do professor.

- [x] Integração Mem0 (memória persistente por aluno; degrada graciosamente sem MEM0_API_KEY)
- [x] `vision_agent.py` (upload e análise de imagens; storage R2 com fallback local em dev)
- [x] `redacao_agent.py` (avaliação ENEM completa, C1–C5 validados em múltiplos de 40, tabela `essays`)
- [x] Sistema de gamificação (XP, badges, streak — seção 8)
- [x] Interface do professor (dashboard de turma, relatório individual, alertas com e-mail opcional)
- [x] RAG com corpus BNCC (pgvector direto, sem LlamaIndex — embeddings via endpoint plugável compatível com OpenAI; ver EMBEDDINGS_* no .env)
- [x] KaTeX no frontend (renderização de matemática)
- [x] Notificações (e-mail via Resend; sem chave, apenas loga)
- [x] Dashboard do aluno completo (XP, streak, badges, evolução de redações)

### FASE 3 — Escala e B2B (Semanas 11–16)
**Objetivo:** Multi-tenant, relatórios avançados, planos e billing.

- [x] Interface do gestor/diretor (heatmap série×matéria, diagnóstico BNCC)
- [x] `report_agent.py` (relatórios pedagógicos via JSON estruturado; exportação em PDF pendente — hoje o frontend renderiza e o navegador imprime)
- [x] Multi-tenancy completo (isolamento por school_id em todos os endpoints; testado)
- [ ] Planos e billing (Stripe) — requer conta Stripe; limite de alunos por plano já é aplicado no backend
- [x] Indexação ENEM/vestibulares no RAG (`scripts/seed_enem.py` — requer JSON com as questões extraídas)
- [x] Mobile responsivo (PWA — manifest + tema; service worker offline pendente)
- [ ] API de integração para sistemas escolares (SIGE, etc.) — aguarda definição dos parceiros
- [x] LGPD compliance (exportação JSON + deleção/anonimização, próprio usuário e via gestor)

---

## 11. VARIÁVEIS DE AMBIENTE (`.env`)

```bash
# Claude Fable 5
ANTHROPIC_API_KEY=sk-ant-...

# Memória
MEM0_API_KEY=m0-...

# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/nerv_ai

# Cache
REDIS_URL=redis://...

# Storage (Cloudflare R2)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=nerv-ai-uploads
R2_PUBLIC_URL=https://uploads.nerv.ai

# Auth
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Email (Resend)
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@nerv.ai

# App
APP_ENV=development  # development | staging | production
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

---

## 12. INSTRUÇÕES ESPECÍFICAS PARA O FABLE 5

> Esta seção orienta o Claude Fable 5 sobre como trabalhar neste repositório.

### O que você pode fazer de forma autônoma:
- Criar e editar qualquer arquivo dentro de `backend/` e `frontend/`
- Executar `alembic upgrade head` após criar migrations
- Executar `pip install` de novas dependências (atualizar `requirements.txt`)
- Executar `npm install` de novas dependências (atualizar `package.json`)
- Rodar o servidor local para testar (`uvicorn main:app --reload`)
- Criar seeds de dados de teste
- Escrever e executar testes com pytest

### Como abordar tarefas complexas:
1. Leia este CLAUDE.md na íntegra antes de iniciar qualquer módulo novo.
2. Para cada módulo, implemente **backend completo** antes de tocar no frontend.
3. Antes de criar qualquer endpoint, garanta que o schema do banco de dados suporte.
4. Use **sempre** o `anthropic_service.py` para chamadas à API — nunca instancie `anthropic.Anthropic()` diretamente em outros módulos.
5. Ao adicionar um novo agente, registre-o neste CLAUDE.md na seção 5.

### Red lines (nunca faça):
- Nunca armazene dados de alunos fora do PostgreSQL isolado por `school_id`.
- Nunca logue conteúdo de mensagens de sessões (apenas metadados e tokens_used).
- Nunca exponha `school_id` ou dados de outros tenants em nenhum endpoint.
- Nunca use modelos diferentes de `claude-fable-5` sem atualizar a const `FABLE_5_MODEL`.

### Prioridade de qualidade:
1. **Funciona corretamente** (testes passam, fluxo funciona end-to-end)
2. **Seguro** (auth, validação, isolamento multi-tenant)
3. **Performático** (queries otimizadas, streaming, cache Redis)
4. **Limpo** (type hints, comentários nos trechos não-óbvios, sem dead code)

---

## 13. TESTES

### Backend (pytest + pytest-asyncio)
```bash
# Rodar todos os testes
pytest backend/tests/ -v

# Testes dos agentes especificamente
pytest backend/tests/test_agents.py -v

# Com coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### Frontend (Vitest + Testing Library)
```bash
cd frontend
npm run test
npm run test:coverage
```

### Teste dos Agentes (manual via script)
```bash
# Testar ciclo completo: sessão → memória → exercício → relatório
python scripts/test_agents.py --student-id test_student_01 --subject matematica --topic funcoes_quadraticas
```

---

## 14. COMO CONTRIBUIR (para o time)

1. Crie uma branch: `feat/nome-do-modulo` ou `fix/descricao-do-bug`
2. Cada PR deve incluir: implementação + testes + atualização do CLAUDE.md se necessário
3. Migrations Alembic sempre em arquivo separado com nome descritivo
4. Nenhum `print()` em produção — use `structlog` ou `logger.info()`
5. Variáveis sensíveis **sempre** via variável de ambiente, nunca hardcoded

---

*Este CLAUDE.md é o documento vivo do projeto. Atualize-o sempre que adicionar um módulo, mudar uma decisão técnica ou corrigir o plano de desenvolvimento.*

*Última atualização: Junho 2026 — Stack atualizada para Claude Fable 5 (lançado 09/06/2026)*
