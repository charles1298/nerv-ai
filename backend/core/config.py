"""Configurações centrais do NERV AI via pydantic-settings.

Todas as variáveis sensíveis vêm do ambiente (.env). Nunca hardcode segredos.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"  # development | staging | production
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Provedor de IA — qualquer API compatível com Chat Completions da OpenAI
    # (OpenAI, Gemini via /v1beta/openai/, Groq, OpenRouter, AI Gateway da Vercel).
    ai_api_key: str = ""
    ai_base_url: str = ""  # vazio = api.openai.com
    ai_model: str = "gemini-3.5-flash"

    # Embeddings para RAG (endpoint compatível com OpenAI /v1/embeddings)
    embeddings_api_url: str = ""
    embeddings_api_key: str = ""
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dim: int = 1536

    # Memória (Mem0 — opcional; sem chave, o tutor roda sem memória de longo prazo)
    mem0_api_key: str = ""

    # Banco de dados
    database_url: str = "postgresql+asyncpg://nerv:nerv@localhost:5432/nerv_ai"

    # Cache / rate limiting
    redis_url: str = "redis://localhost:6379/0"

    # Storage (Cloudflare R2 — sem credenciais, salva em disco local ./uploads)
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "nerv-ai-uploads"
    r2_public_url: str = ""
    local_upload_dir: str = "uploads"

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    jwt_refresh_token_expire_days: int = 30

    # Email (Resend — opcional; sem chave, notificações só logam)
    resend_api_key: str = ""
    email_from: str = "noreply@nerv.ai"

    @field_validator("database_url")
    @classmethod
    def _normalize_pg_url(cls, url: str) -> str:
        """Deixa a DATABASE_URL da hospedagem utilizável pelo asyncpg.

        Duas incompatibilidades que aparecem em Railway, Render, Heroku e Neon:

        1. O esquema vem como `postgresql://` (ou o antigo `postgres://`), que o
           SQLAlchemy async rejeita com um erro de driver pouco óbvio.
        2. A query string vem com `sslmode`/`channel_binding`, parâmetros do
           libpq que o asyncpg não conhece — ele falha com "unexpected keyword
           argument". O asyncpg negocia TLS por conta própria.

        Normalizar aqui vale também para o `alembic upgrade head` do build.
        """
        for prefixo in ("postgresql://", "postgres://"):
            if url.startswith(prefixo):
                url = "postgresql+asyncpg://" + url[len(prefixo) :]
                break

        if not url.startswith("postgresql+asyncpg://") or "?" not in url:
            return url

        base, _, query = url.partition("?")
        incompativeis = {"sslmode", "channel_binding"}
        mantidos = [
            par
            for par in query.split("&")
            if par and par.split("=")[0].lower() not in incompativeis
        ]
        return f"{base}?{'&'.join(mantidos)}" if mantidos else base


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
