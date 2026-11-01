"""The Telegram bot, with Telegram itself replaced by a recording fake (no network, no token, no Gemini)."""

import io

import pytest
import qrcode
from PIL import Image

from app.config import settings
from app.services import ocr, telegram_api, telegram_bot

BOT = "ScamshieldAPIbot"
SCAM = "HSBC Bank: Your account is locked. Verify within 24 hours: https://hbsc-bank.com/login"
GENUINE = "Rs 1,200.00 debited from A/c XX1234 on 31-10-26 via UPI. Ref 612345678901. -HDFC Bank"


class FakeTelegram:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.blocked: set[int] = set()  # people who never pressed Start: a private message to them fails
        self.files: dict[str, bytes] = {}
        self._id = 100

    def __call__(self, method, timeout=20, **params):
        self.calls.append((method, params))
        if method == "getMe":
            return {"ok": True, "result": {"username": BOT}}
        if method == "sendMessage":
            if params["chat_id"] in self.blocked and "ephemeral_message_parameters" not in params:
                return {"ok": False, "error_code": 403, "description": "Forbidden: bot can't initiate conversation with a user"}
            self._id += 1
            return {"ok": True, "result": {"message_id": self._id}}
        return {"ok": True, "result": True}

    def download(self, file_id):
        return self.files.get(file_id)

    def sent(self, method="sendMessage"):
        return [p for m, p in self.calls if m == method]

    def final_text(self):
        """What the person finally sees: the last edit, or the last message sent."""
        edits = self.sent("editMessageText")
        return (edits or self.sent())[-1]["text"]


@pytest.fixture
def tg(monkeypatch):
    fake = FakeTelegram()
    monkeypatch.setattr(settings, "telegram_bot_token", "123456:TEST-TOKEN")
    monkeypatch.setattr(settings, "telegram_allowed_users", "")
    monkeypatch.setattr(settings, "telegram_ephemeral", False)
    monkeypatch.setattr(settings, "telegram_checks_per_hour", 10)
    monkeypatch.setattr(settings, "telegram_checks_per_day", 30)
    monkeypatch.setattr(telegram_api, "call", fake)
    monkeypatch.setattr(telegram_api, "download_file", fake.download)
    telegram_bot._recent_updates.clear()
    telegram_bot._hour.clear()
    telegram_bot._day.clear()
    telegram_bot._username["value"] = None
    return fake


_next = iter(range(1, 10**6))


def private(text=None, user=111, **extra):
    m = {"message_id": 1, "from": {"id": user, "is_bot": False, "username": "tester"}, "chat": {"id": user, "type": "private"}, **extra}
    if text is not None:
        m["text"] = text
    return {"update_id": next(_next), "message": m}


def group(text, user=111, reply=None, entities=None, chat=-500):
    m = {"message_id": 2, "from": {"id": user, "is_bot": False}, "chat": {"id": chat, "type": "supergroup"}, "text": text}
    if entities is not None:
        m["entities"] = entities
    if reply is not None:
        m["reply_to_message"] = reply
    return {"update_id": next(_next), "message": m}


def mention(text):
    start = text.index(f"@{BOT}")
    return [{"type": "mention", "offset": start, "length": len(BOT) + 1}]


def png(draw=None) -> bytes:
    buf = io.BytesIO()
    (draw or Image.new("RGB", (400, 300), "white")).save(buf, "PNG")
    return buf.getvalue()


def qr_png(text: str) -> bytes:
    buf = io.BytesIO()
    qrcode.make(text).save(buf, "PNG")
    return buf.getvalue()


# ----------------------------------------------------------------------------- the webhook

def test_webhook_is_off_without_a_token(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    assert client.post("/telegram/webhook", json={}).status_code == 404


def test_webhook_rejects_calls_that_do_not_carry_the_secret(client, tg):
    assert client.post("/telegram/webhook", json=private("hi")).status_code == 403
    assert client.post("/telegram/webhook", json=private("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "guess"}).status_code == 403
    assert tg.sent() == []


def test_webhook_accepts_telegram_and_answers_the_person(client, tg):
    headers = {"X-Telegram-Bot-Api-Secret-Token": telegram_api.webhook_secret()}
    assert client.post("/telegram/webhook", json=private(SCAM), headers=headers).json() == {"ok": True}
    assert "Dangerous" in tg.final_text()


def test_the_secret_is_valid_for_telegram_and_never_the_token():
    secret = telegram_api.webhook_secret()
    assert secret.isalnum() and len(secret) <= 256 and "TEST" not in secret


# ----------------------------------------------------------------------------- private chat

def test_start_and_help_explain_the_bot(tg):
    telegram_bot.handle_update(private("/start"))
    assert "forward" in tg.final_text().lower() and f"@{BOT}" in tg.final_text()
    telegram_bot.handle_update(private("/help"))
    assert "How to use me" in tg.final_text()


def test_a_scam_gets_a_dangerous_answer_that_edits_the_waiting_message(tg):
    telegram_bot.handle_update(private(SCAM))
    first, = tg.sent()
    assert "Checking" in first["text"]
    edit, = tg.sent("editMessageText")
    assert edit["message_id"] == 101 and edit["chat_id"] == 111
    assert "🔴" in edit["text"] and "Dangerous" in edit["text"] and "<b>What to do</b>" in edit["text"]


def test_links_in_the_answer_cannot_be_tapped(tg):
    telegram_bot.handle_update(private(SCAM))
    text = tg.final_text()
    assert "https://hbsc-bank.com" not in text and "hxxps://hbsc-bank[.]com" in text


def test_a_lookalike_answer_shows_real_versus_fake(tg):
    telegram_bot.handle_update(private(SCAM))
    text = tg.final_text()
    assert "Real vs fake: HSBC" in text and "hsbc.com" in text


def test_a_genuine_notice_is_not_called_a_scam(tg):
    telegram_bot.handle_update(private(GENUINE))
    text = tg.final_text()
    assert "🟢" in text and "Dangerous" not in text


def test_a_command_with_text_checks_that_text(tg):
    telegram_bot.handle_update(private(f"/check {SCAM}"))
    assert "Dangerous" in tg.final_text()


def test_a_link_hidden_behind_text_is_checked(tg):
    text = "Update your KYC now at the HSBC site"
    entities = [{"type": "text_link", "offset": 29, "length": 8, "url": "https://hbsc-bank.com/login"}]
    telegram_bot.handle_update(private(text, entities=entities))
    assert "Dangerous" in tg.final_text()


def test_nothing_to_check_gets_a_hint(tg):
    telegram_bot.handle_update(private("/check"))
    assert "suspicious message" in tg.final_text()


def test_unknown_commands_show_help(tg):
    telegram_bot.handle_update(private("/dance"))
    assert "How to use me" in tg.final_text()


def test_the_bot_ignores_other_bots_and_repeated_updates(tg):
    bot_update = private("hello")
    bot_update["message"]["from"]["is_bot"] = True
    telegram_bot.handle_update(bot_update)
    assert tg.calls == []
    update = private(SCAM)
    telegram_bot.handle_update(update)
    count = len(tg.calls)
    telegram_bot.handle_update(update)  # Telegram resent it because the first reply was slow
    assert len(tg.calls) == count


def test_a_failure_inside_a_check_never_crashes_the_handler(tg, monkeypatch):
    monkeypatch.setattr(telegram_bot, "run_investigation", lambda case: 1 / 0)
    telegram_bot.handle_update(private(SCAM))  # must not raise


# ----------------------------------------------------------------------------- photos

def test_a_photo_of_a_qr_code_is_read_as_a_qr_code(tg, monkeypatch):
    monkeypatch.setattr(ocr, "extract_text", lambda data: ocr.OcrResult("", 0.0, 0))
    tg.files["qr1"] = qr_png("http://hbsc-bank.com/login")
    telegram_bot.handle_update(private(photo=[{"file_id": "small", "width": 90}, {"file_id": "qr1", "width": 800}]))
    assert "Dangerous" in tg.final_text()


def test_a_screenshot_is_read_with_ocr(tg, monkeypatch):
    words = " ".join(["HSBC", "Bank", "your", "account", "is", "locked", "verify", "within", "24", "hours", "at", "https://hbsc-bank.com/login", "now", "please"])
    monkeypatch.setattr(ocr, "extract_text", lambda data: ocr.OcrResult(words, 90.0, 14))
    tg.files["shot"] = png()
    telegram_bot.handle_update(private(photo=[{"file_id": "shot"}]))
    assert "Dangerous" in tg.final_text()


def test_an_image_sent_as_a_file_is_accepted(tg, monkeypatch):
    monkeypatch.setattr(ocr, "extract_text", lambda data: ocr.OcrResult("", 0.0, 0))
    tg.files["doc"] = qr_png("http://hbsc-bank.com/login")
    telegram_bot.handle_update(private(document={"file_id": "doc", "mime_type": "image/png"}))
    assert "Dangerous" in tg.final_text()


def test_an_image_that_cannot_be_downloaded_or_read_is_explained(tg):
    telegram_bot.handle_update(private(photo=[{"file_id": "missing"}]))
    assert "could not download" in tg.final_text()
    tg.files["junk"] = b"not an image"
    telegram_bot.handle_update(private(photo=[{"file_id": "junk"}]))
    assert "Unsupported or corrupt image" in tg.final_text()


# ----------------------------------------------------------------------------- groups

def test_a_group_question_is_answered_privately_not_in_the_group(tg):
    text = f"@{BOT} is this real?"
    telegram_bot.handle_update(group(text, user=222, reply={"message_id": 9, "text": SCAM}, entities=mention(text)))
    assert {p["chat_id"] for p in tg.sent()} == {222}  # only the person's private chat, never the group
    assert "Dangerous" in tg.final_text()


def test_the_reply_target_is_checked_not_the_question(tg):
    text = f"@{BOT} is this real?"
    telegram_bot.handle_update(group(text, reply={"message_id": 9, "text": GENUINE}, entities=mention(text)))
    assert "Dangerous" not in tg.final_text()


def test_a_group_message_that_does_not_address_the_bot_is_ignored(tg):
    telegram_bot.handle_update(group(SCAM))
    telegram_bot.handle_update(group(f"/check@otherbot {SCAM}"))
    assert tg.calls == [("getMe", {})] or all(m == "getMe" for m, _ in tg.calls)


def test_a_group_command_for_this_bot_works(tg):
    telegram_bot.handle_update(group(f"/check@{BOT}", reply={"message_id": 9, "text": SCAM}))
    assert "Dangerous" in tg.final_text()


def test_someone_who_never_pressed_start_is_told_how_in_the_group(tg):
    tg.blocked.add(222)
    text = f"@{BOT} check this"
    telegram_bot.handle_update(group(text, user=222, reply={"message_id": 9, "text": SCAM}, entities=mention(text)))
    note = tg.sent()[-1]
    assert note["chat_id"] == -500 and f"t.me/{BOT}?start=check" in note["text"]
    assert "Dangerous" not in note["text"]
    # nothing was checked, so the turn was not used up
    assert not telegram_bot._hour[222]


def test_ephemeral_replies_are_tried_first_when_switched_on(tg, monkeypatch):
    monkeypatch.setattr(settings, "telegram_ephemeral", True)
    text = f"@{BOT} is this real?"
    telegram_bot.handle_update(group(text, user=222, reply={"message_id": 9, "text": SCAM}, entities=mention(text)))
    sent = tg.sent()
    assert all(p["chat_id"] == -500 and p["ephemeral_message_parameters"] == {"receiver_user_id": 222} for p in sent)
    assert "Dangerous" in sent[-1]["text"] and not tg.sent("editMessageText")


def test_ephemeral_falls_back_to_a_private_chat_if_telegram_refuses(tg, monkeypatch):
    monkeypatch.setattr(settings, "telegram_ephemeral", True)
    original = tg.__call__

    def refuse_ephemeral(method, timeout=20, **params):
        if "ephemeral_message_parameters" in params:
            tg.calls.append((method, params))
            return {"ok": False, "description": "Bad Request: unsupported"}
        return original(method, timeout, **params)

    monkeypatch.setattr(telegram_api, "call", refuse_ephemeral)
    text = f"@{BOT} is this real?"
    telegram_bot.handle_update(group(text, user=222, reply={"message_id": 9, "text": SCAM}, entities=mention(text)))
    assert "Dangerous" in tg.final_text()
    assert tg.sent("editMessageText")[-1]["chat_id"] == 222


# ----------------------------------------------------------------------------- limits and access

def test_each_person_has_their_own_limit(tg, monkeypatch):
    monkeypatch.setattr(settings, "telegram_checks_per_hour", 2)
    ran = []
    real = telegram_bot.run_investigation
    monkeypatch.setattr(telegram_bot, "run_investigation", lambda case: ran.append(1) or real(case))
    for _ in range(3):
        telegram_bot.handle_update(private(GENUINE, user=111))
    assert len(ran) == 2 and "used your checks" in tg.sent()[-1]["text"]
    telegram_bot.handle_update(private(GENUINE, user=333))  # someone else is unaffected
    assert len(ran) == 3


def test_the_limit_resets_after_an_hour():
    telegram_bot._hour.clear()
    telegram_bot._day.clear()
    for i in range(10):
        assert telegram_bot.take_turn(7, now=1000.0 + i) == 0
    assert telegram_bot.take_turn(7, now=1100.0) > 0
    assert telegram_bot.take_turn(7, now=1000.0 + 3700) == 0


def test_an_allow_list_keeps_everyone_else_out(tg, monkeypatch):
    monkeypatch.setattr(settings, "telegram_allowed_users", "tester, 999")
    telegram_bot.handle_update(private(SCAM, user=111))
    assert "Dangerous" in tg.final_text()
    stranger = private(SCAM, user=444)
    stranger["message"]["from"]["username"] = "someone_else"
    before = len(tg.calls)
    telegram_bot.handle_update(stranger)
    assert "limited to a few people" in tg.sent()[-1]["text"] and len(tg.sent("editMessageText")) == 1
    assert len(tg.calls) > before


# ----------------------------------------------------------------------------- the reply text

def test_the_reply_escapes_everything_that_came_from_the_message():
    result = {"verdict": "DANGEROUS", "risk_score": 90, "confidence": 0.9, "category_label": "Phishing <b>",
              "reasons": ["<script>alert(1)</script> & more"], "recommendation": "Do not <click>", "urls": [], "impersonations": []}
    text = telegram_bot.format_result(result)
    assert "<script>" not in text and "&lt;script&gt;" in text and "<click>" not in text


def test_the_reply_always_fits_in_one_telegram_message():
    result = {"verdict": "SUSPICIOUS", "reasons": ["x" * 5000] * 9, "recommendation": "y" * 9000, "urls": [{"url": "https://a.example/" + "z" * 500}] * 9}
    assert len(telegram_bot.format_result(result)) <= 4096


@pytest.mark.parametrize(
    "verdict,assurance,emoji,word",
    [("SAFE", "verified", "🟢", "Safe"), ("SAFE", "promotion", "🔵", "Promotion"), ("SAFE", "spam", "🟣", "Spam"),
     ("SUSPICIOUS", None, "🟠", "Suspicious"), ("DANGEROUS", None, "🔴", "Dangerous"), ("COULD_NOT_VERIFY", None, "⚪", "Could not verify")],
)
def test_colours_match_the_website(verdict, assurance, emoji, word):
    assert telegram_bot._label({"verdict": verdict, "assurance": assurance}) == (emoji, word)


def test_no_em_dashes_in_what_the_bot_says():
    assert "—" not in telegram_bot.START_TEXT + telegram_bot.HELP_TEXT + telegram_bot.FOOTER


# ----------------------------------------------------------------------------- start-up and safety

def test_the_token_is_never_logged_by_the_http_library():
    import logging

    assert logging.getLogger("httpx").level >= logging.WARNING


def test_registration_sets_the_webhook_with_the_secret(tg, monkeypatch):
    from app.api import telegram as api

    monkeypatch.setattr(settings, "telegram_public_url", "https://example.onrender.com/")
    api.register()
    hook, = tg.sent("setWebhook")
    assert hook["url"] == "https://example.onrender.com/telegram/webhook"
    assert hook["secret_token"] == telegram_api.webhook_secret() and hook["allowed_updates"] == ["message"]
    assert tg.sent("setMyCommands")


def test_registration_needs_an_https_address_and_a_token(tg, monkeypatch):
    from app.api import telegram as api

    monkeypatch.setattr(settings, "telegram_public_url", None)
    monkeypatch.setattr(settings, "render_external_url", None)
    api.register()
    assert not tg.sent("setWebhook")
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "telegram_public_url", "https://example.onrender.com")
    api.register()
    assert not tg.sent("setWebhook")
