"""Telegram bot (long polling). Run next to the server, or as a separate process.

Env:
  TELEGRAM_BOT_TOKEN  - from @BotFather
  TELEGRAM_ALLOWED_IDS - comma-separated numeric chat IDs allowed to use the bot (IMPORTANT)
"""
import os
import time

import httpx

import agent as core

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED = {int(x) for x in os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",") if x.strip()}
API = f"https://api.telegram.org/bot{TOKEN}"


def send(chat_id: int, text: str):
    for i in range(0, len(text), 3900):  # Telegram message limit ~4096
        httpx.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text[i:i + 3900]}, timeout=30)


def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN missing")
    offset = 0
    history: dict[int, list] = {}
    print("Telegram bot polling...")
    while True:
        try:
            r = httpx.get(f"{API}/getUpdates", params={"timeout": 50, "offset": offset}, timeout=60)
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if not chat_id or not text:
                    continue
                if ALLOWED and chat_id not in ALLOWED:
                    send(chat_id, f"Access denied. Your chat id is {chat_id}.")
                    continue
                if text in ("/start", "/help"):
                    send(chat_id, "Ami tomar agent. Likho ja chao. Example: search: AI news\n"
                                  "fetch: https://... | read: file.txt | shell: ls | apk")
                    continue
                h = history.setdefault(chat_id, [])
                out = core.run_agent(text, h)
                h += [{"role": "user", "content": text},
                      {"role": "assistant", "content": out["reply"]}]
                history[chat_id] = h[-20:]
                send(chat_id, out["reply"] or "(empty reply)")
        except Exception as e:  # noqa: BLE001
            print("error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
