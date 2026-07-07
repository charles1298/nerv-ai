"""Sessões de tutoria com streaming SSE do Fable 5.

Red line (seção 12): nunca logar conteúdo das mensagens — apenas metadados.
"""

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.tutor_agent import generate_session_insights, run_tutor_turn
from core.database import get_db
from memory.mem0_client import save_session_insights
from services.gamification_service import award_xp
from services.performance_service import record_session
from core.security import rate_limit, require_role
from models import SessionMessage, TutoringSession, User
from schemas.sessions import ChatMessageRequest, MessagePublic, SessionCreateRequest, SessionPublic

logger = structlog.get_logger()
router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _get_owned_session(
    session_id: uuid.UUID, student: User, db: AsyncSession
) -> TutoringSession:
    session = await db.scalar(
        select(TutoringSession)
        .options(
            selectinload(TutoringSession.subject),
            selectinload(TutoringSession.topic),
            selectinload(TutoringSession.messages),
        )
        .where(TutoringSession.id == session_id, TutoringSession.student_id == student.id)
    )
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada")
    return session


@router.post("", response_model=SessionPublic, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> TutoringSession:
    session = TutoringSession(
        student_id=student.id,
        subject_id=body.subject_id,
        topic_id=body.topic_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("session_started", session_id=str(session.id), student_id=str(student.id))
    return session


@router.get("", response_model=list[SessionPublic])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[TutoringSession]:
    result = await db.scalars(
        select(TutoringSession)
        .where(TutoringSession.student_id == student.id)
        .order_by(TutoringSession.started_at.desc())
    )
    return list(result)


@router.get("/{session_id}/messages", response_model=list[MessagePublic])
async def get_messages(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> list[SessionMessage]:
    session = await _get_owned_session(session_id, student, db)
    return session.messages


@router.post("/{session_id}/chat", dependencies=[Depends(rate_limit("tutoring_messages"))])
async def chat(
    session_id: uuid.UUID,
    body: ChatMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> StreamingResponse:
    """Envia mensagem do aluno e devolve a resposta do tutor via SSE.

    Persiste a mensagem do aluno antes do stream e a resposta completa ao final.
    """
    session = await _get_owned_session(session_id, student, db)
    if session.ended_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Sessão já encerrada")

    history = list(session.messages)
    user_msg = SessionMessage(session_id=session.id, role="user", content=body.content)
    session.messages_count += 2  # user + assistant
    db.add(user_msg)
    await db.commit()

    async def event_stream() -> AsyncGenerator[str, None]:
        full_response: list[str] = []
        try:
            async for chunk in run_tutor_turn(student, session, history, body.content, db=db):
                full_response.append(chunk)
                # JSON-encode preserva quebras de linha dentro do frame SSE
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("tutor_stream_failed", session_id=str(session.id), error=str(e))
            yield "event: error\ndata: Falha ao gerar resposta. Tente novamente.\n\n"
            return
        finally:
            if full_response:
                assistant_msg = SessionMessage(
                    session_id=session.id,
                    role="assistant",
                    content="".join(full_response),
                )
                db.add(assistant_msg)
                await db.commit()
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{session_id}/end", response_model=SessionPublic)
async def end_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> TutoringSession:
    session = await _get_owned_session(session_id, student, db)
    if session.ended_at is None:
        session.ended_at = datetime.now(timezone.utc)

        # Fase 2: insights pedagógicos → Mem0 + gamificação + performance.
        # Tudo tolerante a falha — encerrar sessão nunca depende de serviços externos.
        insights, quality_score = await generate_session_insights(student, session.messages)
        session.insights = insights
        session.quality_score = quality_score
        if insights:
            await save_session_insights(str(student.id), insights)

        await award_xp(db, student.id, "sessao_completada")
        await record_session(db, student.id, session.subject_id)

        await db.commit()
        await db.refresh(session)
    logger.info(
        "session_ended",
        session_id=str(session.id),
        messages_count=session.messages_count,
        tokens_used=session.tokens_used,
        insights_count=len(session.insights or []),
    )
    return session
