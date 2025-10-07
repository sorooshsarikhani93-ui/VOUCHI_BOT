import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMIN_ID, LOG_CHANNEL
from store import PRODUCTS, categories_list
from utils import format_price, create_and_send_otp, verify_otp_code, create_pay_ir_link
from storage import upsert_user, get_user

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# in-memory temp map for KYC flow (ok for single-instance MVP)
TEMP = {}

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('🛍 فروشگاه')
    kb.add('👤 حساب کاربری')
    return kb

@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    upsert_user(msg.from_user.id, phone=None, verified=False)
    await msg.answer('سلام! به Vouchi خوش آمدی 🙂\nبرای شروع از منوی پایین استفاده کن.', reply_markup=main_keyboard())

@dp.message_handler(lambda m: m.text == '🛍 فروشگاه')
async def show_categories(msg: types.Message):
    cats = categories_list()
    kb = types.InlineKeyboardMarkup()
    for cat in cats.keys():
        kb.add(types.InlineKeyboardButton(cat, callback_data=f'cat:{cat}'))
    await msg.answer('دسته‌بندی‌ها:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('cat:'))
async def cat_click(call: types.CallbackQuery):
    cat = call.data.split(':',1)[1]
    cats = categories_list()
    kb = types.InlineKeyboardMarkup()
    for p in cats.get(cat, []):
        kb.add(types.InlineKeyboardButton(p['name'], callback_data=f'prod:{p["sku"]}'))
    await call.message.answer(f'📂 {cat}:', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('prod:'))
async def prod_click(call: types.CallbackQuery):
    sku = call.data.split(':',1)[1]
    product = PRODUCTS.get(sku)
    if not product:
        await call.answer('محصول یافت نشد', show_alert=True); return
    text = f"<b>{product['name']}</b>\n\n{format_price(product['price_usd'])}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('💳 پرداخت ریالی', callback_data=f'buy:rial:{sku}'))
    kb.add(types.InlineKeyboardButton('🪙 پرداخت کریپتو (آتی)', callback_data=f'buy:crypto:{sku}'))
    await bot.send_photo(call.from_user.id, product['image'], caption=text, parse_mode='HTML', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('buy:'))
async def buy_flow(call: types.CallbackQuery):
    _, method, sku = call.data.split(':',2)
    user = get_user(call.from_user.id)
    if not user or not user.get('verified'):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton('ارسال شماره', request_contact=True))
        await call.message.answer('برای خرید لطفا ابتدا شماره همراه‌تان را ارسال کنید تا کد تایید برایتان ارسال شود.', reply_markup=kb)
        return
    product = PRODUCTS.get(sku)
    if method == 'rial':
        amount_rial = product['price_usd'] * float(os.getenv('USD_TO_RIAL', '126000'))
        link = await create_pay_ir_link(amount_rial, product['name'])
        if link:
            await call.message.answer_photo(product['image'],
                                            caption=f"✅ آماده پرداخت:\n{product['name']}\n{format_price(product['price_usd'])}",
                                            reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('پرداخت (باز شدن در مرورگر)', url=link)))
            await bot.send_message(ADMIN_ID, f"سفارش ایجادشده (در انتظار پرداخت):\nکاربر: {call.from_user.full_name} ({call.from_user.id})\nمحصول: {product['name']}\nقیمت: {product['price_usd']} USD")
        else:
            await call.message.answer('⚠️ خطا در ایجاد لینک پرداخت. لطفا بعدا تلاش کنید.')
    else:
        await call.message.answer('پرداخت کریپتو در MVP بعدی فعال می‌شود.')

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(msg: types.Message):
    contact = msg.contact
    if contact.user_id != msg.from_user.id:
        await msg.answer('لطفا از دکمه ارسال شماره استفاده کنید تا شماره خودتان ارسال شود.')
        return
    phone = contact.phone_number
    TEMP[msg.from_user.id] = {'phone': phone}
    ok, reason = await create_and_send_otp(msg.from_user.id, phone)
    if not ok:
        if reason == 'cooldown':
            await msg.answer('کد قبلی هنوز تازه است. لطفاً چند لحظه صبر کنید و دوباره تلاش کنید.')
        else:
            await msg.answer('ارسال پیامک با خطا مواجه شد. لطفاً بعدا تلاش کنید.')
        return
    await msg.answer('کد تایید به شمارهٔ همراه شما ارسال شد. لطفاً کد 6 رقمی را در همین چت ارسال کنید.')

@dp.message_handler(lambda m: m.text and m.from_user.id in TEMP)
async def otp_input_handler(m: types.Message):
    code = m.text.strip()
    ok, reason = await verify_otp_code(m.from_user.id, code)
    if ok:
        phone = TEMP[m.from_user.id]['phone']
        upsert_user(m.from_user.id, phone=phone, verified=True)
        TEMP.pop(m.from_user.id, None)
        await m.answer('✅ احراز هویت انجام شد. اکنون می‌توانید خرید کنید.', reply_markup=main_keyboard())
        await bot.send_message(ADMIN_ID, f'کاربر {m.from_user.full_name} ({m.from_user.id}) احراز هویت شد. شماره: {phone}')
    else:
        if reason == 'expired':
            TEMP.pop(m.from_user.id, None)
            await m.answer('کد منقضی شده. لطفاً مجدد درخواست شماره و ارسال کد دهید.')
        elif reason == 'wrong':
            await m.answer('کد اشتباه است. دوباره تلاش کنید.')
        elif reason == 'too_many':
            TEMP.pop(m.from_user.id, None)
            await m.answer('تعداد تلاش‌ها بیش از حد شد. لطفاً ۱۵ دقیقه دیگر تلاش کنید.')
        else:
            await m.answer('خطایی رخ داد. لطفاً دوباره تلاش کنید.')

@dp.message_handler(lambda m: m.text == '👤 حساب کاربری')
async def account_info(m: types.Message):
    user = get_user(m.from_user.id)
    if not user:
        await m.answer('حسابی یافت نشد. لطفا /start را بزنید.')
        return
    txt = f"👤 شناسه: {m.from_user.id}\nتلفن: {user.get('phone','-')}\nوضعیت احراز: {'✅' if user.get('verified') else '❌'}"
    await m.answer(txt)

if __name__ == '__main__':
    TEMP = {}
    executor.start_polling(dp, skip_updates=True)
