import os
import logging
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------- health server for Render Web Service ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logger.info("Health server running on port %s", PORT)
    server.serve_forever()


# ---------- helper functions ----------
def format_name(user) -> str:
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full_name or "No Name"


def format_username(user) -> str:
    return f"@{user.username}" if user.username else "No Username"


def format_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_member(status: str) -> bool:
    return status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.RESTRICTED,
    )


# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 Hello! ကြိုဆိုပါတယ်\n\n"
        "🤖 Welcome Bot Activated!\n"
        "━━━━━━━━━━━━━━━\n"
        "✅ Auto Welcome Message\n"
        "✅ Auto Goodbye Message\n"
        "✅ ID / Username / Name / Date ပြပေးမယ်\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⚙️ အသုံးပြုနည်း\n"
        "1️⃣ Bot ကို Group ထဲ add လုပ်ပါ\n"
        "2️⃣ Bot ကို Admin ပေးပါ\n"
        "3️⃣ Member Join / Leave ဖြစ်တာနဲ့ Auto Message ပို့ပါမယ်\n\n"
        "❗ IMPORTANT\n"
        "Bot ကို Admin မပေးရင် Join/Leave updates မရနိုင်ပါ\n\n"
        "🚀 Ready ဖြစ်ပြီဆိုရင် Group ထဲ add လုပ်ပြီး Admin ပေးလိုက်ပါ!"
    )
    await update.message.reply_text(text)


# ---------- join / leave handler ----------
async def welcome_left(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = update.chat_member
    if not cm:
        return

    old_status = cm.old_chat_member.status
    new_status = cm.new_chat_member.status
    user = cm.new_chat_member.user
    chat_id = cm.chat.id

    was_member = is_member(old_status)
    now_member = is_member(new_status)

    text = None

    if not was_member and now_member:
        text = (
            "🎉 ကြိုဆိုပါတယ် 🎉\n\n"
            f"🆔 ID - {user.id}\n"
            f"👤 Username - {format_username(user)}\n"
            f"☑️ Name - {format_name(user)}\n"
            f"🗓️ Date - {format_date()}\n\n"
            "😊 Welcome!"
        )
    elif was_member and not now_member:
        text = (
            "👋 နုတ်ဆက်ပါတယ်\n\n"
            f"🆔 ID - {user.id}\n"
            f"👤 Username - {format_username(user)}\n"
            f"☑️ Name - {format_name(user)}\n"
            f"🗓️ Date - {format_date()}\n\n"
            "😔 Goodbye"
        )

    if text:
        await context.bot.send_message(chat_id=chat_id, text=text)


def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(welcome_left, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Bot starting with polling...")
    app.run_polling(
        allowed_updates=["message", "chat_member"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
