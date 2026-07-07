# NERV AI — Entrega do Marco: Mês 2

> **Marco:** Mês 2 — Desenvolvimento da base do sistema e estrutura inicial da aplicação
> **Status:** Concluído
> **Projeto:** NERV AI — Sistema de Inteligência Educacional Adaptativa (alinhado à BNCC)

---

## 1. Entregável

**Descrição do marco:** *Desenvolvimento da base do sistema e estrutura inicial da aplicação.*

A base do sistema foi desenvolvida com arquitetura cliente-servidor completa, organizada em três camadas:

### Backend (API) — Python 3.12 + FastAPI
Estrutura modular já implementada:

| Camada | Conteúdo |
|---|---|
| `core/` | Configuração, conexão com banco (SQLAlchemy async), segurança (JWT + bcrypt), rate limiting |
| `models/` | Modelo de dados completo (escolas, usuários, matérias, tópicos, sessões, exercícios, tentativas) |
| `routers/` | Endpoints REST por domínio: autenticação, usuários, matérias, sessões de tutoria, exercícios |
| `agents/` | Agentes de IA (tutor, exercícios) — base do diferencial pedagógico |
| `services/` | Integração com o provedor de IA (configurável por ambiente) |
| `schemas/` | Validação de dados de entrada e saída (Pydantic v2) |

### Frontend (Aplicação Web) — Next.js 14 + TypeScript
- Estrutura de rotas por perfil (aluno, professor/gestor, autenticação)
- Tela de login funcional
- Interface de tutoria, exercícios e painéis
- Identidade visual própria aplicada (tema escuro, paleta da marca)

### Infraestrutura
- Ambiente de desenvolvimento containerizado (`docker-compose.yml`)
- Arquivos de deploy prontos (Railway/Vercel)
- Scripts de carga inicial de dados (`seed_dev.py`)

**Conclusão:** a fundação técnica sobre a qual as próximas funcionalidades serão construídas está estabelecida e operacional.

---

## 2. Evidência Esperada

**Descrição do marco:** *Repositório do projeto com primeiras funcionalidades implementadas.*

### 2.1 Repositório
O código-fonte está versionado em repositório Git, com histórico de commit e organização de pastas padronizada (ver seção 1). Estrutura de diretórios:

```
nerv-ai/
├── backend/     API FastAPI (core, models, routers, agents, services, schemas, tests)
├── frontend/    Aplicação Next.js (login, tutoria, exercícios, painéis)
├── infra/       Docker Compose, Dockerfiles, configs de deploy
├── scripts/     Carga de dados de desenvolvimento
└── docs/        Documentação e entregas de marcos
```

### 2.2 Primeiras funcionalidades implementadas
| # | Funcionalidade | Situação |
|---|---|---|
| 1 | Cadastro de escola e usuário administrador | ✅ Implementado |
| 2 | Autenticação (login) com token JWT e refresh | ✅ Implementado |
| 3 | Controle de acesso por perfil (aluno, professor, gestor, admin) | ✅ Implementado |
| 4 | Cadastro e listagem de usuários por escola | ✅ Implementado |
| 5 | Catálogo de matérias e tópicos (base BNCC) | ✅ Implementado |
| 6 | Sessão de tutoria com resposta em tempo real (streaming) | ✅ Implementado |
| 7 | Geração de exercícios adaptativos | ✅ Implementado |
| 8 | Registro e correção de tentativas de exercício | ✅ Implementado |
| 9 | Painel do professor (visão da turma) | ✅ Implementado |

### 2.3 Qualidade — testes automatizados
A suíte de testes do backend cobre autenticação, controle de acesso e os agentes:

```
pytest tests/ -q
28 passed
```

---

## 3. Critério de Aceite

**Descrição do marco:** *Sistema inicia corretamente e permite navegação básica.*

### 3.1 Sistema inicia corretamente
- **Backend:** sobe em `http://localhost:8000` e responde no endpoint de verificação de saúde:
  ```
  GET /health  →  {"status":"ok","env":"development"}
  ```
- **Frontend:** sobe em `http://localhost:3000` (Next.js pronto, páginas compiladas com sucesso).
- **Banco de dados:** criado e populado com dados de demonstração (escola, usuários e matérias).

### 3.2 Permite navegação básica
Fluxo verificado de ponta a ponta:
1. Acesso à aplicação → redirecionamento para a tela de **Login**.
2. Login com credenciais válidas → autenticação bem-sucedida (token emitido).
3. Navegação entre as áreas conforme o perfil:
   - **Aluno:** Início → Tutoria → Exercícios → Redação
   - **Professor/Gestor:** Dashboard da Turma → Visão da Escola

### 3.3 Credenciais de demonstração
| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@demo.nerv.ai` | `aluno-demo-123` |
| Professor | `professora@demo.nerv.ai` | `prof-demo-123` |
| Gestor/Admin | `admin@demo.nerv.ai` | `admin-demo-123` |

**Resultado:** o sistema inicia corretamente e a navegação básica entre as telas está funcional. Critério **atendido**.

---

## 4. Como executar (reprodutível)

```bash
# Backend
cd backend
.venv\Scripts\activate
uvicorn main:app --reload            # http://localhost:8000

# Dados de demonstração
python ..\scripts\seed_dev.py

# Frontend
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

---

*Documento de evidência do Marco Mês 2 — NERV AI.*
