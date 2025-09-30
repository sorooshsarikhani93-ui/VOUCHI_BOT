import logging
from aiogram import Bot, Dispatcher, types, executor
from config import TELEGRAM_TOKEN, ADMIN_ID, LOG_CHANNEL
from store import CATEGORIES
from utils import format_price

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# شروع
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES.keys():
        keyboard.add(cat)
    await message.answer("به فروشگاه Vouchi خوش آمدید 🛒\nلطفا دسته‌بندی را انتخاب کنید:", reply_markup=keyboard)

# انتخاب دسته‌بندی
@dp.message_handler(lambda m: m.text in CATEGORIES.keys())
async def category_handler(message: types.Message):
    cat = message.text
    for product in CATEGORIES[cat]:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💵 پرداخت ریالی", callback_data=f"pay_rial:{product['id']}"))
        kb.add(types.InlineKeyboardButton("💳 پرداخت کریپتو", callback_data=f"pay_usd:{product['id']}"))

        text = f"📦 {product['name']}\n\n{format_price(product['price_usd'])}"
        await message.answer_photo(product['image'], caption=text, reply_markup=kb)

# پردازش کلیک روی دکمه
@dp.callback_query_handler(lambda c: c.data.startswith("pay_"))
async def payment_handler(callback: types.CallbackQuery):
    method, pid = callback.data.split(":")
    # پیدا کردن محصول
    for cat in CATEGORIES.values():
        for product in cat:
            if product["id"] == pid:
                # اطلاع به ادمین
                pay_type = "ریالی" if method == "pay_rial" else "کریپتو"
                msg = f"🆕 سفارش جدید\n\nکاربر: {callback.from_user.full_name} ({callback.from_user.id})\nمحصول: {product['name']}\nروش پرداخت: {pay_type}\n{format_price(product['price_usd'])}"
                await bot.send_message(ADMIN_ID, msg)
                if LOG_CHANNEL:
                    await bot.send_message(LOG_CHANNEL, msg)

                await callback.message.answer("✅ سفارش شما ثبت شد. تیم ما به زودی با شما تماس می‌گیرد.")
                await callback.answer()
                return
