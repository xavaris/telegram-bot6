import os
import sqlite3
import asyncio
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BACKUP_TOPIC = int(os.getenv("BACKUP_TOPIC"))

GROUP_ID = -1003569725744
DB_FILE = "users.db"

BACKUP_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔔 Zapisz się na backup",
     url="https://t.me/Backupklaunybot?start=backup")]
])

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user(user):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, first_name, last_seen)
        VALUES (?, ?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def count_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return total

# ================= GROUP LISTENER =================
async def group_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        save_user(update.message.from_user)

# ================= /START =================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "backup" in update.message.text:
        save_user(update.message.from_user)
        await update.message.reply_text(
            "✅ Zostałeś zapisany do systemu backupu.\n"
            "Jeśli grupa padnie — dostaniesz nowy link."
        )
    else:
        await update.message.reply_text("👋 Witaj!")

# ================= DAILY REMINDER =================
async def reminder_loop(app):
    await asyncio.sleep(10)
    while True:
        await app.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=BACKUP_TOPIC,
            text="🔔 Kliknij aby zapisać się na backup grupy:",
            reply_markup=BACKUP_BUTTON
        )
        await asyncio.sleep(60 * 60 * 24)

# ================= /NOTIFYALL =================
async def notify_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
