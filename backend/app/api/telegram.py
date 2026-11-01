"""The Telegram webhook: Telegram posts every message sent to the bot here."""

import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.config import settings
from app.services import telegram_api, telegram_bot

router = APIRouter()
log = logging.getLogger("scamshield.telegram")

COMMANDS = [
    {"command": "start", "description": "What this bot does"},
    {"command": "check", "description": "Check a message (or reply to one with /check)"},
    {"command": "help", "description": "How to use it"},
]
SHORT_DESCRIPTION = "Forward me a suspicious message, screenshot or QR photo and I will tell you if it looks like a scam."
DESCRIPTION = (
    "ScamShield checks messages, links, screenshots and QR codes for scams and phishing. "
    "Forward or paste anything suspicious, or send a screenshot or a photo of a QR code, and get a plain answer in seconds. "
    "Nothing is stored. An automated assessment, not a guarantee."
)


@router.post("/telegram/webhook")
async def webhook(request: Request, tasks: BackgroundTasks):
    if not telegram_api.enabled():
        raise HTTPException(status_code=404, detail="Not found")
    supplied = request.headers.get("x-telegram-bot-api-secret-token", "")
    if not hmac.compare_digest(supplied, telegram_api.webhook_secret()):
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        update = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Bad request") from None
    if isinstance(update, dict):
        tasks.add_task(telegram_bot.handle_update, update)  # the reply takes seconds; Telegram only needs a quick 200
    return {"ok": True}


def register() -> None:
    """On start-up: tell Telegram where to send updates, and set the bot's commands and description. Best effort."""
    if not telegram_api.enabled():
        return
    base = (settings.telegram_public_url or settings.render_external_url or "").rstrip("/")
    if not base.startswith("https://"):
        log.info("telegram: no public https address known, webhook not registered")
        return
    hook = telegram_api.call("setWebhook", url=f"{base}/telegram/webhook", secret_token=telegram_api.webhook_secret(), allowed_updates=["message"], max_connections=10)
    log.info("telegram: webhook %s", "registered" if hook.get("ok") else f"not registered ({hook.get('description')})")
    telegram_api.call("setMyCommands", commands=COMMANDS)
    telegram_api.call("setMyShortDescription", short_description=SHORT_DESCRIPTION)
    telegram_api.call("setMyDescription", description=DESCRIPTION)
