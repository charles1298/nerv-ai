"""Schemas Pydantic das sessões de tutoria."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    subject_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None


class SessionPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    student_id: uuid.UUID
    subject_id: uuid.UUID | None
    topic_id: uuid.UUID | None
    started_at: datetime
    ended_at: datetime | None
    messages_count: int


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class MessagePublic(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    role: str
    content: str
    content_type: str
    created_at: datetime
