import os
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, CallbackQueryHandler
)
from mcrcon import MCRcon
import psutil

# ===== CONFIG =====
TOKEN = "8735701354:AAGzxTKxaPUZ17aPNQA-0azzM8PFnHw5huQ"
OWNER_ID = 1915732631

RCON_HOST = "127.0.0.1"
RCON_PORT = 25642
RCON_PASSWORD = "tOOX9GB3I5"

LOG_FILE = "bot.log"
DB_FILE = "db.json"
MC_LOG = "logs/latest.log"  # путь к логам сервера

# ===== DB =====
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "admins": [OWNER_ID],
            "mods": [5099481771],
            "broadcasts": [],
            "autorestart": 0
        }
    with open(DB_FILE) as f:
        return json.load(f)

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

db = load_db()

# ===== UTILS =====
def log(text):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {text}\n")

def rcon(cmd):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as m:
            return m.command(cmd)
    except Exception as e:
        return str(e)

def is_admin(uid):
    return uid in db["admins"] or uid == OWNER_ID

def is_mod(uid):
    return uid in db["mods"] or is_admin(uid)

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📊 Статус", callback_data="status")],
        [InlineKeyboardButton("👥 Онлайн", callback_data="online")],
        [InlineKeyboardButton("🔄 Рестарт", callback_data="restart")]
    ]
    await update.message.reply_text("Панель:", reply_markup=InlineKeyboardMarkup(kb))

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("❌")

    command = " ".join(context.args)
    log(f"{uid}: {command}")
    await update.message.reply_text(rcon(command))

async def online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(rcon("list"))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    await update.message.reply_text(f"CPU: {cpu}% RAM: {ram}%")

async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_mod(update.effective_user.id):
        return
    text = " ".join(context.args)
    rcon(f"say {text}")
    await update.message.reply_text("OK")

# ===== ADMINS =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    uid = int(context.args[0])
    db["admins"].append(uid)
    save_db()
    await update.message.reply_text("admin added")

async def add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    db["mods"].append(uid)
    save_db()
    await update.message.reply_text("mod added")

# ===== LOGS =====
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not os.path.exists(LOG_FILE):
        return await update.message.reply_text("no logs")

    with open(LOG_FILE) as f:
        lines = f.readlines()[-10:]
    await update.message.reply_text("".join(lines))

# ===== AUTO =====
async def broadcaster():
    while True:
        for msg in db["broadcasts"]:
            rcon(f"say {msg}")
        await asyncio.sleep(300)

async def autorestart():
    while True:
        if db["autorestart"] > 0:
            await asyncio.sleep(db["autorestart"])
            rcon("say Restarting...")
            rcon("stop")
        await asyncio.sleep(10)

# ===== MC LOG WATCHER =====
async def watch_logs(app):
    if not os.path.exists(MC_LOG):
        return

    with open(MC_LOG, "r") as f:
        f.seek(0, 2)

        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(1)
                continue

            if "joined the game" in line:
                await app.bot.send_message(OWNER_ID, f"🟢 {line}")

            if "left the game" in line:
                await app.bot.send_message(OWNER_ID, f"🔴 {line}")

# ===== BUTTONS =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_mod(q.from_user.id):
        return await q.edit_message_text("❌")

    if q.data == "status":
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        await q.edit_message_text(f"CPU: {cpu}% RAM: {ram}%")

    elif q.data == "online":
        await q.edit_message_text(rcon("list"))

    elif q.data == "restart":
        rcon("say restarting...")
        rcon("stop")
        await q.edit_message_text("server stopped")

# ===== INIT =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cmd", cmd))
app.add_handler(CommandHandler("online", online))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("say", say))
app.add_handler(CommandHandler("addadmin", add_admin))
app.add_handler(CommandHandler("addmod", add_mod))
app.add_handler(CommandHandler("logs", logs))
app.add_handler(CallbackQueryHandler(buttons))

# запуск фоновых задач
app.create_task(broadcaster())
app.create_task(autorestart())
app.create_task(watch_logs(app))

print("V4 BOT STARTED")
app.run_polling()
