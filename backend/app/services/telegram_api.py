"""
A very small Telegram Bot API client (plain HTTPS calls, no extra library).

The bot token is part of every request address, so nothing here ever logs an address, and errors are reduced to the
description Telegram sends back.
"""

import hashlib
import hmac
import logging

import httpx

from app.config import settings

# httpx logs full request addresses at INFO level, and the address contains the token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

API = "https://api.telegram.org"
MAX_DOWNLOAD = 8 * 1024 * 1024
log = logging.getLogger("scamshield.telegram")


def enabled() -> bool:
    return bool(settings.telegram_bot_token)


def webhook_secret() -> str:
    """Derived from the token, so there is nothing extra to configure. Telegram sends it back on every call."""
    key = (settings.telegram_bot_token or "").encode()
    return hmac.new(key, b"scamshield-telegram-webhook", hashlib.sha256).hexdigest()[:48]


def call(method: str, timeout: float = 20, **params) -> dict:
    """Call one Bot API method. Never raises: a failure comes back as {"ok": False, "description": ...}."""
    try:
        response = httpx.post(f"{API}/bot{settings.telegram_bot_token}/{method}", json=params, timeout=timeout)
        data = response.json()
        return data if isinstance(data, dict) else {"ok": False, "description": "unexpected reply"}
    except Exception as err:  # noqa: BLE001
        log.warning("telegram call %s failed: %s", method, type(err).__name__)
        return {"ok": False, "description": type(err).__name__}


def download_file(file_id: str) -> bytes | None:
    """Fetch a file a user sent (Telegram allows bots up to 20 MB; the checker accepts up to 8 MB)."""
    info = call("getFile", file_id=file_id)
    path = (info.get("result") or {}).get("file_path")
    size = (info.get("result") or {}).get("file_size") or 0
    if not info.get("ok") or not path or size > MAX_DOWNLOAD:
        return None
    try:
        response = httpx.get(f"{API}/file/bot{settings.telegram_bot_token}/{path}", timeout=30)
        if response.status_code != 200 or len(response.content) > MAX_DOWNLOAD:
            return None
        return response.content
    except Exception as err:  # noqa: BLE001
        log.warning("telegram download failed: %s", type(err).__name__)
        return None
