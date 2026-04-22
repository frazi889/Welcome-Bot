import os
import logging
import asyncio
from datetime import datetime, timezone

from flask import Flask, request
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

PORT = int(os.getenv("PORT", "10000"))
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET missing")

if not BASE_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL missing")

WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# =========================
# LOG
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# APP
# =========================
flask_app = Flask(__name__)
ptb_app = Application.builder().token(BOT_TOKEN).build()

# =========================
# FUNCTIONS
# =========================
def format_name(user):
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or "No Name"

def format_username(user):
    return f"@{user.username}" if user.username else "No Username"

def format_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def is_member(status):
    return status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.RESTRICTED,
    )

# =========================
# /start COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! ကြိုဆိုပါတယ်\n\n"
        "🤖 Welcome Bot Activated!\n"
        "━━━━━━━━━━━━━━━\n"
        "✅ Auto Welcome Message\n"
        "✅ Auto Goodbye Message\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⚙️ အသုံးပြုနည်း\n"
        "1️⃣ Bot ကို Group ထဲ add လုပ်ပါ\n"
        "2️⃣ Bot ကို Admin ပေးပါ\n"
        "3️⃣ Member Join / Leave ဖြစ်တာနဲ့ Auto Message ပို့ပါမယ်\n\n"
        "❗ IMPORTANT\n"
        "Bot ကို Admin မပေးရင် အလုပ်မလုပ်ပါ\n\n"
        "🚀 Ready ဖြစ်ပြီဆိုရင် Group ထဲ add လုပ်လိုက်ပါ!"
    )

# =========================
# WELCOME / GOODBYE
# =========================
async def welcome_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm = update.chat_member
    if not cm:
        return

    old = cm.old_chat_member.status
    new = cm.new_chat_member.status
    user = cm.new_chat_member.user
    chat_id = cm.chat.id

    was = is_member(old)
    now = is_member(new)

    text = ""

    if not was and now:
        text = f"""🎉 ကြိုဆိုပါတယ် 🎉

🆔 ID - {user.id}
👤 Username - {format_username(user)}
☑️ Name - {format_name(user)}
🗓️ Date - {format_date()}

😊 Welcome!"""

    elif was and not now:
        text = f"""👋 နုတ်ဆက်ပါတယ်

🆔 ID - {user.id}
👤 Username - {format_username(user)}
☑️ Name - {format_name(user)}
🗓️ Date - {format_date()}

😔 Goodbye"""

    if text:
        await context.bot.send_message(chat_id, text)

# =========================
# HANDLERS
# =========================
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(ChatMemberHandler(welcome_left, ChatMemberHandler.CHAT_MEMBER))

# =========================
# ROUTES
# =========================
@flask_app.get("/")
def home():
    return "Bot running"

@flask_app.post(WEBHOOK_PATH)
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return "ok"

# =========================
# START
# =========================
async def main():
    await ptb_app.initialize()
    await ptb_app.start()

    await ptb_app.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=["message", "chat_member"],
        drop_pending_updates=True,
    )

asyncio.run(main())

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=PORT)
