"""Estado de gamificação do aluno — XP, streak e badges (seção 8)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import require_role
from models import User
from services.gamification_service import BADGES_BY_ID, get_or_create_gamification

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me")
async def my_gamification(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role("student"))],
) -> dict:
    gam = await get_or_create_gamification(db, student.id)
    await db.commit()
    return {
        "xp_total": gam.xp_total,
        "streak_days": gam.streak_days,
        "last_activity_date": gam.last_activity_date.isoformat() if gam.last_activity_date else None,
        "badges": [
            {
                "id": badge_id,
                "name": BADGES_BY_ID[badge_id]["name"],
            }
            for badge_id in (gam.badges or [])
            if badge_id in BADGES_BY_ID
        ],
    }
