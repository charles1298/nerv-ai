"""Configurações centrais do NERV AI via pydantic-settings.

Todas as variáveis sensíveis vêm do ambiente (.env). Nunca hardcode segredos.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"  # development | staging | production
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Provedor de IA (qualquer API compatível com a Messages API da Anthropic)
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""  # vazio = api.anthropic.com
    ai_model: str = "claude-fable-5"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
