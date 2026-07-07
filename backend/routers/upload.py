"""Upload multimodal: aluno fotografa prova/caderno → análise por visão (seção 5.4)."""

import base64
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.vision_agent import analyze_uploaded_image
from core.database import get_db
from core.security import rate_limit, require_role
from memory.mem0_client import get_student_context
from models import TutoringSession, Upload, User
from services.storage_service import public_url, store_file

logger = structlog.get_logger()
router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("", dependencies=[Depends(rate_limit("image_uploads"))], status_code=status.HTTP_201_CREATED)
async def upload_image(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
    file: Annotated[UploadFile, File()],
    prompt: Annotated[str, Form()] = "",
    session_id: Annotated[str | None, Form()] = None,
) -> dict:
    """Recebe a foto, armazena (R2/local), analisa com visão e persiste o resultado."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Formato não suportado. Use: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem acima de 5 MB")
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Arquivo vazio")

    linked_session_id: uuid.UUID | None = None
    if session_id:
        try:
            parsed = uuid.UUID(session_id)
        except ValueError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "session_id inválido") from e
        session = await db.scalar(
            select(TutoringSession).where(
                TutoringSession.id == parsed, TutoringSession.student_id == student.id
            )
        )
        if session is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada")
        linked_session_id = session.id

    r2_key = await store_file(data, file.filename or "foto.jpg", file.content_type, str(student.id))

    student_context = await get_student_context(str(student.id), prompt or "análise de imagem")
    try:
        result = await analyze_uploaded_image(
            image_base64=base64.b64encode(data).decode(),
            mime_type=file.content_type,
            student_prompt=prompt,
            student_context=student_context,
            student_id=str(student.id),
        )
    except Exception as e:
        logger.error("vision_analysis_failed", student_id=str(student.id), error=str(e))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Falha na análise da imagem. Tente novamente."
        ) from e

    upload = Upload(
        student_id=student.id,
        session_id=linked_session_id,
        filename=file.filename or "foto.jpg",
        r2_key=r2_key,
        mime_type=file.content_type,
        analysis_result=result,
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)
    logger.info("upload_analyzed", upload_id=str(upload.id), student_id=str(student.id))

    return {
        "upload_id": str(upload.id),
        "url": public_url(r2_key),
        "analysis": result["analysis"],
    }
