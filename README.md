# NERV AI — Sistema de Inteligência Educacional Adaptativa

Plataforma SaaS multi-tenant de tutoria adaptativa para escolas brasileiras, alinhada à BNCC.
Especificação completa em [CLAUDE.md](CLAUDE.md).

**Status:** Fases 1, 2 e 3 implementadas — tutoria com memória (Mem0) e RAG, visão multimodal,
correção de redação ENEM, gamificação, dashboards de professor e gestor, LGPD.
Pendentes: deploy (Railway/Vercel), billing Stripe e API de integração escolar.

## Stack

- **Backend:** Python 3.12 · FastAPI · SQLAlchemy 2 (async) · PostgreSQL (pgvector) · Redis
- **IA:** **provedor trocável via env** — qualquer API compatível com Chat Completions da OpenAI
  (Gemini, OpenAI, Groq, AI Gateway da Vercel) via `AI_BASE_URL`, `AI_API_KEY` e `AI_MODEL`.
  Embeddings do RAG via endpoint compatível com OpenAI (`EMBEDDINGS_*`).
- **Frontend:** Next.js 14 (App Router) · Tailwind · Zustand · KaTeX · PWA

## Rodando localmente

### Opção A — Docker Compose (tudo)

```bash
cp .env.example .env       # preencha AI_API_KEY e JWT_SECRET_KEY
cd infra
docker compose up --build
```

- Backend: http://localhost:8000 (docs em `/docs`)
- Frontend: http://localhost:3000

### Opção B — Dev manual

```bash
# Banco e cache
cd infra && docker compose up db redis -d

# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Seed de dados demo (escola, usuários, matérias)
python ..\scripts\seed_dev.py

# Frontend
cd frontend
npm install
npm run dev
```

**Logins demo (após o seed):**

| Papel | E-mail | Senha |
|---|---|---|
| Aluno | aluno@demo.nerv.ai | aluno-demo-123 |
| Professora | professora@demo.nerv.ai | prof-demo-123 |
| Admin | admin@demo.nerv.ai | admin-demo-123 |

## Testes

```bash
cd backend
pytest tests/ -v                 # 28 testes (auth, agentes, redação, gamificação, upload, LGPD)

# Ciclo real dos agentes (requer API key de IA configurada)
python ..\scripts\test_agents.py --topic "Funções quadráticas"
```

## RAG (opcional)

Com `EMBEDDINGS_API_URL`/`EMBEDDINGS_API_KEY` configurados:

```bash
python ..\scripts\seed_bncc.py                       # amostra BNCC embutida
python ..\scripts\seed_bncc.py --file corpus.json    # corpus completo
python ..\scripts\seed_enem.py --file questoes.json  # banco ENEM
```

Sem embeddings configurados, o tutor funciona normalmente, apenas sem grounding no corpus.

## Estrutura

```
backend/    FastAPI — core/, agents/, models/, routers/, schemas/, services/, tests/
frontend/   Next.js — src/app/ (login, chat, exercícios), components/, lib/, store/
infra/      docker-compose, Dockerfiles, railway.toml
scripts/    seed_dev.py, test_agents.py
```

## Trocando o provedor de IA

Toda chamada de modelo passa por `backend/services/ai_service.py`. No `.env`:

```bash
AI_API_KEY=sua-chave
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/   # vazio = OpenAI
AI_MODEL=gemini-3.5-flash
```

Nenhum agente precisa ser alterado.

## Pendências (ver CLAUDE.md seção 10)

Deploy Railway/Vercel (arquivos prontos em `infra/`) · billing Stripe ·
API de integração escolar (SIGE) · service worker offline do PWA · exportação PDF nativa.
