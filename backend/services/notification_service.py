"""Notificações por e-mail via Resend. Sem RESEND_API_KEY, apenas loga (dev)."""

import httpx
import structlog

from core.config import settings

logger = structlog.get_logger()

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html: str) -> bool:
    """Envia e-mail. Retorna False (sem levantar) quando desativado ou em falha."""
    if not settings.resend_api_key:
        logger.info("email_skipped_no_api_key", to=to, subject=subject)
        return False
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.email_from,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            resp.raise_for_status()
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as e:
        logger.error("email_failed", to=to, error=str(e))
        return False
