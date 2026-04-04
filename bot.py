import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

TOKEN = "8762834034:AAHrG05E0BUgCU2jRfoigSDtOtO-cJ4Zj5Q"
ADMIN_ID = 1915732631 # вставь свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== ТОВАРЫ ======
products = {
    "osint": [
        ("Деанонизация", "3$"),
        ("Геоинт по фото", "5$")
    ],
    "esim": [
        ("eSIM Нидерланды (7 дней)", "2$"),
        ("eSIM Россия", "3$"),
        ("eSIM ОАЭ", "4$")
    ],
    "bots": [
        ("Лёгкий бот", "3$"),
        ("Средний бот", "6$"),
        ("Сложный бот", "8$")
    ]
}

# ====== КНОПКИ ======
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Купить")],
        [KeyboardButton(text="💰 Прайс"), KeyboardButton(text="📞 Поддержка")]
    ],
    resize_keyboard=True
)

# ====== СТАРТ ======
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "⚡ Быстрые цифровые услуги\n"
        "⏳ Выполнение от 5 минут\n\n"
        "Выбери действие 👇",
        reply_markup=main_kb
    )

# ====== КАТАЛОГ ======
@dp.message(F.text == "🛒 Купить")
async def catalog(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Услуги", callback_data="cat_osint")],
        [InlineKeyboardButton(text="📱 eSIM", callback_data="cat_esim")],
        [InlineKeyboardButton(text="🤖 Боты", callback_data="cat_bots")]
    ])
    await message.answer("Выбери категорию:", reply_markup=kb)

# ====== ПОКАЗ ТОВАРОВ ======
@dp.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    items = products.get(category, [])

    for name, price in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Купить", callback_data=f"buy_{name}")]
        ])

        await callback.message.answer(
            f"🔥 {name}\n💰 Цена: {price}\n\n"
            f"✔ Быстрое выполнение\n"
            f"⏳ Осталось мест: 3",
            reply_markup=kb
        )

# ====== ПОКУПКА ======
@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):
    product = callback.data.replace("buy_", "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатил", callback_data=f"paid_{product}")]
    ])

    await callback.message.answer(
        f"🧾 Ты выбрал: {product}\n\n"
        f"💳 Оплати и нажми кнопку ниже\n\n"
        f"⚠ После оплаты заказ сразу уходит в работу",
        reply_markup=kb
    )

# ====== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ======
@dp.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery):
    product = callback.data.replace("paid_", "")
    user = callback.from_user

    # сообщение пользователю
    await callback.message.answer(
        "✅ Платёж принят\n"
        "⏳ Заказ передан исполнителю\n"
        "Среднее время: 5–30 минут"
    )

    # сообщение админу
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый заказ!\n\n"
        f"👤 @{user.username}\n"
        f"📦 Товар: {product}"
    )

# ====== ПРАЙС ======
@dp.message(F.text == "💰 Прайс")
async def price(message: Message):
    await message.answer(
        "💰 Прайс:\n\n"
        "Деанонизация — 3$\n"
        "Геоинт — 5$\n\n"
        "eSIM:\n"
        "Нидерланды — 2$\n"
        "Россия — 3$\n"
        "ОАЭ — 4$"
    )

# ====== ПОДДЕРЖКА ======
@dp.message(F.text == "📞 Поддержка")
async def support(message: Message):
    await message.answer("Напиши сюда: @your_username")

# ====== ЗАПУСК ======
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
