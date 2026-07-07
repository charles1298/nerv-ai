"""Storage de uploads — Cloudflare R2 (S3-compatible) com fallback em disco local.

Com credenciais R2 no env, usa boto3; sem elas (dev local), grava em
./uploads — mesma interface, troca transparente.
"""

import asyncio
import uuid
from pathlib import Path

import structlog

from core.config import settings

logger = structlog.get_logger()


def r2_enabled() -> bool:
    return bool(
        settings.r2_account_id and settings.r2_access_key_id and settings.r2_secret_access_key
    )


def _r2_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


async def store_file(data: bytes, filename: str, mime_type: str, student_id: str) -> str:
    """Persiste o arquivo e retorna a chave (r2_key) para a tabela uploads."""
    key = f"{student_id}/{uuid.uuid4()}-{filename}"

    if r2_enabled():
        client = _r2_client()
        await asyncio.to_thread(
            client.put_object,
            Bucket=settings.r2_bucket_name,
            Key=key,
            Body=data,
            ContentType=mime_type,
        )
        logger.info("upload_stored_r2", key=key, bytes=len(data))
    else:
        path = Path(settings.local_upload_dir) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        logger.info("upload_stored_local", key=key, bytes=len(data))

    return key


def public_url(key: str) -> str:
    """URL pública do arquivo (R2 com CDN, ou caminho local em dev)."""
    if r2_enabled() and settings.r2_public_url:
        return f"{settings.r2_public_url.rstrip('/')}/{key}"
    return f"{settings.backend_url}/{settings.local_upload_dir}/{key}"
