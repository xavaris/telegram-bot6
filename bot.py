import os
import sqlite3
import asyncio
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BACKUP_TOPIC = int(os.getenv("BACKUP_TOPIC"))

GROUP_ID = -1003569725744
DB_FILE = "users.db"

BACKUP_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔔 Zapisz się na backup", url="https://t.me/BotDoWeryfikacjiBot?start=backup")]
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
    result = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return result

# ================= GROUP LISTENER =================
async def group_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        save_user(update.message.from_user)

# ================= /START =================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "backup" in update.message.text:
        save_user(update.message.from_user)
        await update.message.reply_text("✅ Zapisano Cię do systemu backupu.")
    else:
        await update.message.reply_text(
            "👋 Witaj!\n"
            "Kliknij przycisk w grupie aby zapisać się do systemu backupu."
        )

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
        return

    if not context.args:
        await update.message.reply_text("Użycie:\n/notifyall LINK")
        return

    link = context.args[0]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    users = c.execute("SELECT user_id FROM users").fetchall()
    conn.close()

    sent = 0

    for (uid,) in users:
        try:
            await context.bot.send_message(uid, f"🚨 NOWA GRUPA:\n{link}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Wysłano do {sent} użytkowników.")

# ================= /STATS =================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    total = count_users()
    await update.message.reply_text(
        f"📊 STATYSTYKI BACKUPU\n\n"
        f"👥 Zapisanych użytkowników: {total}"
    )

# ================= MAIN =================
def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, group_listener))
    app.add_handler(MessageHandler(filters.Regex("^/start"), start_handler))
    app.add_handler(CommandHandler("notifyall", notify_all))
    app.add_handler(CommandHandler("stats", stats))

    asyncio.get_event_loop().create_task(reminder_loop(app))

    print("BACKUP BOT STARTED")
    app.run_polling()

# ================= RUN =================
if __name__ == "__main__":
    main()
