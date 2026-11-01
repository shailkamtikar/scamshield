"""
Try the Telegram bot from your own computer, without a public address.

    cd backend && uv run python scripts/telegram_poll.py

It reads TELEGRAM_BOT_TOKEN from backend/.env, removes the bot's webhook, and then asks Telegram for new messages every
few seconds. Press Ctrl+C to stop.

Careful: a bot has one webhook. Running this switches the deployed bot off until the deployed server restarts (it
registers the webhook again when it starts). Use a second bot from @BotFather if the deployed bot must stay up.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import telegram_api, telegram_bot  # noqa: E402


def main() -> None:
    if not telegram_api.enabled():
        sys.exit("Set TELEGRAM_BOT_TOKEN in backend/.env first.")
    me = telegram_api.call("getMe")
    if not me.get("ok"):
        sys.exit(f"Telegram refused the token: {me.get('description')}")
    print(f"Connected as @{me['result']['username']}. Send it a message. Ctrl+C to stop.")
    telegram_api.call("deleteWebhook")
    offset = None
    while True:
        try:
            reply = telegram_api.call("getUpdates", offset=offset, allowed_updates=["message"])
            for update in reply.get("result") or []:
                offset = update["update_id"] + 1
                telegram_bot.handle_update(update)
        except KeyboardInterrupt:
            print("Stopped.")
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
