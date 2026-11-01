"""
The ScamShield Telegram bot.

People forward or paste a suspicious message, send a screenshot or a photo of a QR code, or (in a group) reply to the
message with a mention of the bot. The bot runs the same investigation as the website and answers privately.

What it relies on, and what it never does:
- Telegram calls the webhook (app/api/telegram.py); everything here runs after the 200 reply has gone back.
- Only the sender of a request gets the answer. In a group the answer goes to the person's private chat (they must have
  pressed Start once) or, if switched on, to a Telegram "ephemeral" message that only they can see.
- Nothing is stored: no message text, no files. Only counters per person, in memory, to protect the free quotas.
- Links in a reply are defanged so a tap cannot open them.
"""

import html
import logging
import re
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.api._shared import run_investigation
from app.api.investigate_image import build_case
from app.api.investigate_qr import MAX_CODES, _investigate_codes
from app.api.uploads import validate_image
from app.config import settings
from app.engine.analysis import Case
from app.intel.urls import extract_urls
from app.services import ocr, telegram_api
from app.services.qr import decode_all

log = logging.getLogger("scamshield.telegram")

MAX_TEXT = 40_000
SCREENSHOT_WORDS = 12  # a photo with more text than this is read as a screenshot even if it also holds a code
FOOTER = "Automated assessment, not a guarantee. If you lost money, call 1930 or report at cybercrime.gov.in."

START_TEXT = (
    "Hi, I am ScamShield. I check whether a message, link, screenshot or QR code looks safe.\n\n"
    "Send or forward me anything suspicious: a text, an email, a screenshot, or a photo of a QR code. "
    "I will answer in 5 to 15 seconds.\n\n"
    "In a group, reply to the suspicious message with @{username} and I will answer you privately. "
    "I can only message you privately after you have pressed Start here once.\n\n"
    "I do not keep your messages. " + FOOTER
)
HELP_TEXT = (
    "How to use me:\n"
    "1. Forward or paste a suspicious message here.\n"
    "2. Or send a screenshot, or a photo of a QR code.\n"
    "3. In a group, reply to the message with @{username}.\n\n"
    "I never open a link on your phone. Links in my answers are written like hxxps://example[.]com so they cannot be tapped by mistake."
)

_lock = threading.Lock()
_recent_updates: deque[int] = deque(maxlen=1000)
_hour: dict[int, deque] = defaultdict(deque)
_day: dict[int, deque] = defaultdict(deque)
_busy = threading.BoundedSemaphore(3)  # the free server is small; extra checks wait their turn
_username: dict[str, str | None] = {"value": None}


# ----------------------------------------------------------------------------- small helpers

def bot_username() -> str:
    if not _username["value"]:
        me = telegram_api.call("getMe")
        _username["value"] = (me.get("result") or {}).get("username") or ""
    return _username["value"] or ""


def seen_before(update_id: int | None) -> bool:
    """Telegram resends an update when a reply is slow (for example while the server wakes up)."""
    if update_id is None:
        return False
    with _lock:
        if update_id in _recent_updates:
            return True
        _recent_updates.append(update_id)
        return False


def allowed(user: dict) -> bool:
    wanted = {item.strip().lower().lstrip("@") for item in settings.telegram_allowed_users.split(",") if item.strip()}
    if not wanted:
        return True
    return str(user.get("id")) in wanted or str(user.get("username", "")).lower() in wanted


def take_turn(user_id: int, now: float | None = None) -> int:
    """Use one of the person's checks. Returns 0 when allowed, else the minutes to wait."""
    now = time.time() if now is None else now
    with _lock:
        hour, day = _hour[user_id], _day[user_id]
        while hour and now - hour[0] > 3600:
            hour.popleft()
        while day and now - day[0] > 86400:
            day.popleft()
        if len(hour) >= settings.telegram_checks_per_hour:
            return int((3600 - (now - hour[0])) // 60) + 1
        if len(day) >= settings.telegram_checks_per_day:
            return int((86400 - (now - day[0])) // 60) + 1
        hour.append(now)
        day.append(now)
        if len(_hour) > 20_000:
            _hour.clear()
            _day.clear()
        return 0


def give_back(user_id: int) -> None:
    with _lock:
        for used in (_hour[user_id], _day[user_id]):
            if used:
                used.pop()


def _slice(text: str, offset: int, length: int) -> str:
    """Telegram counts entity positions in UTF-16 code units."""
    raw = text.encode("utf-16-le")
    return raw[offset * 2:(offset + length) * 2].decode("utf-16-le", "ignore")


def _entities(message: dict) -> list[dict]:
    return message.get("entities") or message.get("caption_entities") or []


def _text_of(message: dict) -> str:
    return message.get("text") or message.get("caption") or ""


def _is_mention(message: dict, username: str) -> bool:
    text = _text_of(message)
    return any(e.get("type") == "mention" and _slice(text, e["offset"], e["length"]).lower() == f"@{username}".lower() for e in _entities(message))


def _command(message: dict, username: str) -> tuple[str, str] | None:
    """('start' | 'help' | 'check' | other, rest of the text) when the text is a command meant for this bot."""
    m = re.match(r"^/(\w+)(?:@(\w+))?(?:\s+(.*))?$", _text_of(message).strip(), re.S)
    if not m:
        return None
    if m.group(2) and m.group(2).lower() != username.lower():
        return None
    return m.group(1).lower(), (m.group(3) or "").strip()


def _hidden_links(message: dict) -> list[str]:
    text = _text_of(message)
    return [e["url"] for e in _entities(message) if e.get("type") == "text_link" and e.get("url") and e["url"] not in text]


def _content_text(message: dict, username: str) -> str:
    """The wording plus the real target of any link whose shown text hides it."""
    text = re.sub(rf"@{re.escape(username)}\b", " ", _text_of(message), flags=re.I) if username else _text_of(message)
    text = re.sub(r"^/\w+(?:@\w+)?\s*", "", text.strip())
    hidden = _hidden_links(message)
    if hidden:
        text += "\n\nLinks behind the text:\n" + "\n".join(hidden[:12])
    return text.strip()[:MAX_TEXT]


def _image_id(message: dict) -> str | None:
    photos = message.get("photo")
    if photos:
        return photos[-1].get("file_id")  # the largest size comes last
    doc = message.get("document") or {}
    if str(doc.get("mime_type", "")).startswith("image/"):
        return doc.get("file_id")
    return None


# ----------------------------------------------------------------------------- the reply text

def _label(result: dict) -> tuple[str, str]:
    verdict, assurance = result.get("verdict"), result.get("assurance")
    if verdict == "SAFE":
        return {
            "verified": ("🟢", "Safe"),
            "valid_payment": ("🟢", "Valid payment request"),
            "no_links": ("🟢", "Clear"),
            "spam": ("🟣", "Spam"),
            "promotion": ("🔵", "Promotion"),
            "promotion_unverified": ("🔵", "Promotion"),
        }.get(assurance, ("🟢", "Clear" if assurance else "Safe"))
    return {"SUSPICIOUS": ("🟠", "Suspicious"), "DANGEROUS": ("🔴", "Dangerous")}.get(verdict, ("⚪", "Could not verify"))


def esc(text: str) -> str:
    """Telegram's HTML only needs & < > escaped (quotes stay as they are)."""
    return html.escape(str(text), quote=False)


def defang(url: str, limit: int = 90) -> str:
    out = re.sub(r"^http", "hxxp", url.strip(), flags=re.I).replace(".", "[.]")
    return out[:limit] + ("..." if len(out) > limit else "")


def _clip(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 3].rstrip() + "..."


def format_result(result: dict) -> str:
    """The answer, as Telegram HTML. Every piece of text from the analysis is escaped."""
    e = esc
    emoji, word = _label(result)
    lines = [f"{emoji} <b>{e(word)}</b>"]
    score, conf = result.get("risk_score"), result.get("confidence")
    meta = []
    if score is not None:
        meta.append(f"Risk {int(score)}/100")
    if conf is not None:
        meta.append(f"confidence {round(float(conf) * 100)}%")
    if result.get("category_label") and result["category_label"] != word:
        meta.append(e(str(result["category_label"])))
    if meta:
        lines.append(" · ".join(meta))

    reasons = [r for r in (result.get("reasons") or []) if str(r).strip()][:5]
    if reasons:
        lines += ["", "<b>Why</b>"] + [f"• {e(_clip(r, 230))}" for r in reasons]

    for item in (result.get("impersonations") or [])[:2]:
        real = item.get("official") or []
        if real and item.get("shown"):
            lines += ["", f"<b>Real vs fake: {e(str(item.get('brand', '')))}</b>",
                      f"Real: {e(', '.join(real[:2]))}",
                      f"This message: {e(defang(str(item['shown'])))}"]

    links = [u.get("final_url") or u.get("url") or u.get("original") for u in (result.get("urls") or [])]
    links = [defang(str(u)) for u in links if u][:3]
    if result.get("decoded_text") and not links:
        links = [defang(str(result["decoded_text"]))]
    if links:
        lines += ["", "<b>Links checked</b> (written so they cannot be tapped)"] + [f"• {e(u)}" for u in links]

    if result.get("recommendation"):
        lines += ["", "<b>What to do</b>", e(_clip(result["recommendation"], 400))]
    lines += ["", f"<i>{e(FOOTER)}</i>"]
    return "\n".join(lines)[:4000]


# ----------------------------------------------------------------------------- sending

class Where:
    """Where one answer goes: a private chat (the first message is edited into the answer) or a group-only "ephemeral" message."""

    def __init__(self, chat_id: int = 0, message_id: int | None = None, ephemeral_in: int | None = None, user_id: int = 0):
        self.chat_id, self.message_id, self.ephemeral_in, self.user_id = chat_id, message_id, ephemeral_in, user_id

    def __bool__(self) -> bool:
        return bool(self.chat_id or self.ephemeral_in)


def _send(chat_id: int, text: str, **extra) -> dict:
    return telegram_api.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML", link_preview_options={"is_disabled": True}, **extra)


def _ephemeral(group: int, user_id: int, text: str) -> dict:
    return _send(group, text, ephemeral_message_parameters={"receiver_user_id": user_id})


def open_reply(group_chat: int | None, user_id: int, text: str) -> Where:
    """Send the first message. A group question is answered privately, so the group never sees it."""
    if group_chat is not None and settings.telegram_ephemeral and _ephemeral(group_chat, user_id, text).get("ok"):
        return Where(ephemeral_in=group_chat, user_id=user_id)
    first = _send(user_id, text)
    if first.get("ok"):
        return Where(chat_id=user_id, message_id=(first.get("result") or {}).get("message_id"), user_id=user_id)
    if group_chat is not None:
        link = f"https://t.me/{bot_username()}?start=check"
        _send(group_chat, f'I can only answer privately after you press Start once: <a href="{link}">open the chat with me</a>, press Start, then ask again.')
    return Where()


def finish_reply(where: Where, text: str) -> None:
    if where.ephemeral_in:
        _ephemeral(where.ephemeral_in, where.user_id, text)
        return
    if where.message_id:
        edited = telegram_api.call("editMessageText", chat_id=where.chat_id, message_id=where.message_id, text=text, parse_mode="HTML", link_preview_options={"is_disabled": True})
        if edited.get("ok"):
            return
    _send(where.chat_id, text)


# ----------------------------------------------------------------------------- the checks

def check_image(data: bytes) -> dict:
    """A photo is a QR code when it is mostly a code, and a screenshot otherwise."""
    data, mime = validate_image(data)
    codes = decode_all(data)
    if codes:
        try:
            words = ocr.extract_text(data).words
        except ocr.OcrUnavailable:
            words = 0
        if words < SCREENSHOT_WORDS:
            return _investigate_codes(codes[:MAX_CODES], None)
    return run_investigation(build_case(data, mime, None, "telegram"))


def analyse(target: dict, username: str) -> dict | str:
    """The result, or a short sentence saying why nothing could be checked."""
    file_id = _image_id(target)
    try:
        if file_id:
            data = telegram_api.download_file(file_id)
            if not data:
                return "I could not download that image. It may be too large (the limit is 8 MB). Try sending it again as a photo."
            return check_image(data)
        text = _content_text(target, username)
        if len(text) < 2:
            return "I could not find anything to check in that message. Send the text, a link, a screenshot or a QR photo."
        return run_investigation(Case(message=text, source="telegram", kind="text"))
    except HTTPException as err:
        return str(err.detail)


# ----------------------------------------------------------------------------- the entry point

def handle_update(update: dict) -> None:
    """Handle one update from Telegram. Never raises."""
    try:
        _handle(update)
    except Exception:  # noqa: BLE001
        log.exception("telegram update failed")


def _handle(update: dict) -> None:
    message = update.get("message")
    if not message or seen_before(update.get("update_id")):
        return
    user = message.get("from") or {}
    if not user.get("id") or user.get("is_bot"):
        return
    username = bot_username()
    chat = message.get("chat") or {}
    private = chat.get("type") == "private"
    group_chat = None if private else chat.get("id")
    user_id = user["id"]

    command = _command(message, username)
    if not private and not command and not _is_mention(message, username):
        return  # in a group the bot only reacts when it is addressed

    def say(text: str) -> None:
        open_reply(group_chat, user_id, esc(text))

    if not allowed(user):
        say("This bot is limited to a few people for now. Please use the website instead: https://scamshield-smoky.vercel.app/")
        return
    if command and command[0] in {"start", "help"}:
        open_reply(group_chat, user_id, esc((START_TEXT if command[0] == "start" else HELP_TEXT).format(username=username or "this_bot")))
        return
    if command and command[0] != "check":
        open_reply(group_chat, user_id, esc(HELP_TEXT.format(username=username or "this_bot")))
        return

    # What to check: the message being replied to when someone asks about it, otherwise what they sent themselves.
    reply = message.get("reply_to_message")
    own = bool(_content_text(message, username) or _image_id(message))
    if reply and (not private or command or not own):
        target = reply
    elif own:
        target = message
    else:
        say("Send me the suspicious message, a screenshot or a QR photo, or reply to it with my @name, and I will check it.")
        return

    wait = take_turn(user_id)
    if wait:
        say(f"You have used your checks for now. Please try again in about {wait} minutes, or use the website: https://scamshield-smoky.vercel.app/")
        return
    where = open_reply(group_chat, user_id, "Checking it now. This takes 5 to 15 seconds...")
    if not where:
        give_back(user_id)  # nothing was checked, so the turn is not used
        return
    with _busy:
        outcome = analyse(target, username)
    finish_reply(where, esc(outcome) if isinstance(outcome, str) else format_result(outcome))
