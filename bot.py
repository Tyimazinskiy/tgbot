import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
from mcrcon import MCRcon
import psutil

# ===== НАСТРОЙКИ =====
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OWNER_ID = 123456789

RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "your_rcon_password"

DB_FILE = "db.json"

# ===== БАЗА ДАННЫХ =====
def load_db():
    if not os.path.exists(DB_FILE):
        return {"admins": [OWNER_ID]}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

db = load_db()

def is_admin(user_id):
    return user_id in db["admins"] or user_id == OWNER_ID

# ===== RCON =====
def send_rcon(command):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(command)
    except Exception as e:
        return f"Ошибка RCON: {e}"

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data="status")],
        [InlineKeyboardButton("👥 Онлайн", callback_data="online")],
        [InlineKeyboardButton("🔄 Рестарт", callback_data="restart")]
    ]

    await update.message.reply_text(
        "🎮 Панель управления сервером:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Нет доступа")

    if not context.args:
        return await update.message.reply_text("⚠️ Укажи команду")

    command = " ".join(context.args)
    response = send_rcon(command)

    await update.message.reply_text(f"📨 {response}")

async def online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    response = send_rcon("list")
    await update.message.reply_text(response)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    await update.message.reply_text(f"CPU: {cpu}%\nRAM: {ram}%")

async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        return await update.message.reply_text("⚠️ Укажи текст")

    text = " ".join(context.args)
    send_rcon(f"say {text}")

    await update.message.reply_text("✅ Отправлено")

# ===== АДМИНЫ =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        return await update.message.reply_text("Укажи ID")

    uid = int(context.args[0])

    if uid not in db["admins"]:
        db["admins"].append(uid)
        save_db()

    await update.message.reply_text("✅ Админ добавлен")

async def del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        return await update.message.reply_text("Укажи ID")

    uid = int(context.args[0])

    if uid == OWNER_ID:
        return await update.message.reply_text("❌ Нельзя удалить владельца")

    if uid in db["admins"]:
        db["admins"].remove(uid)
        save_db()

    await update.message.reply_text("🗑 Админ удалён")

# ===== КНОПКИ =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return await query.edit_message_text("❌ Нет доступа")

    if query.data == "status":
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        await query.edit_message_text(f"CPU: {cpu}%\nRAM: {ram}%")

    elif query.data == "online":
        response = send_rcon("list")
        await query.edit_message_text(response)

    elif query.data == "restart":
        send_rcon("say Сервер перезапускается...")
        send_rcon("stop")
        await query.edit_message_text("🔄 Сервер остановлен")

# ===== ЗАПУСК =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cmd", cmd))
app.add_handler(CommandHandler("online", online))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("say", say))
app.add_handler(CommandHandler("addadmin", add_admin))
app.add_handler(CommandHandler("deladmin", del_admin))
app.add_handler(CallbackQueryHandler(buttons))

print("✅ Бот запущен")
app.run_polling()