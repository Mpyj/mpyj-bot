import random
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


async def send_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال کپچا"""
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b
    
    options = [answer]
    while len(options) < 4:
        wrong = random.randint(2, 20)
        if wrong not in options:
            options.append(wrong)
    
    random.shuffle(options)
    
    context.user_data["captcha_answer"] = answer
    context.user_data["captcha_time"] = time.time()
    
    keyboard = []
    row = []
    for opt in options:
        row.append(InlineKeyboardButton(
            str(opt),
            callback_data=f"captcha_{opt}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    await update.message.reply_text(
        f"🤖 **کپچا امنیتی**\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"برای اطمینان از ربات نبودن،\n"
        f"جواب درست رو انتخاب کن:\n\n"
        f"❓ **{a} + {b} = ?**\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⏱️ فقط ۲ دقیقه وقت داری",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def verify_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی جواب کپچا"""
    query = update.callback_query
    await query.answer()
    
    try:
        answer = int(query.data.replace("captcha_", ""))
    except:
        await query.answer("❌ خطا!", show_alert=True)
        return
    
    correct = context.user_data.get("captcha_answer")
    captcha_time = context.user_data.get("captcha_time", 0)
    
    # چک کن کپچا منقضی نشده (۲ دقیقه)
    if time.time() - captcha_time > 120:
        await query.edit_message_text(
            "⏱️ کپچا منقضی شد!\n\n👉 /start رو بزن"
        )
        return
    
    if answer != correct:
        await query.answer("❌ اشتباه! دوباره تلاش کن", show_alert=True)
        return
    
    # ✅ کپچا درست
    await query.answer("✅ درست بود!", show_alert=True)
    
    context.user_data.pop("captcha_answer", None)
    context.user_data.pop("captcha_time", None)
    
    # ذخیره زمان کپچا در دیتابیس
    from database import get_user, update_last_captcha
    from config import OWNER_TELEGRAM_ID
    from commands.helpers import MAIN_MENU, ADMIN_MENU
    
    user_id = query.from_user.id
    existing = get_user(user_id)
    
    if existing:
        update_last_captcha(user_id)
    
    if existing:
        # کاربر قبلی → منو
        menu = ADMIN_MENU if user_id == OWNER_TELEGRAM_ID else MAIN_MENU
        await query.edit_message_text(
            f"✅ **کپچا تایید شد!**\n\n"
            f"✨ خوش برگشتی {query.from_user.first_name} 👋",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text="از منوی زیر انتخاب کن 👇",
            reply_markup=menu
        )
    else:
        # کاربر جدید → ثبت‌نام
        keyboard = [
            [InlineKeyboardButton("🚀 ساخت کیف پول", callback_data="create_account")],
            [InlineKeyboardButton("📖 راهنمای ربات", callback_data="help")]
        ]
        await query.edit_message_text(
            f"✅ **کپچا تایید شد!**\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💎 به Mpyj Coin خوش اومدی\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"برای شروع، یه کیف پول برات می‌سازیم 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )