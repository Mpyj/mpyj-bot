import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


async def send_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال کپچا برای کاربر جدید"""
    # ساخت دو عدد تصادفی
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b
    
    # ساخت ۴ گزینه (یکی درست، ۳ تا غلط)
    options = [answer]
    while len(options) < 4:
        wrong = random.randint(2, 20)
        if wrong not in options:
            options.append(wrong)
    
    random.shuffle(options)
    
    # ذخیره جواب درست
    context.user_data["captcha_answer"] = answer
    context.user_data["captcha_passed"] = False
    
    # ساخت کیبورد
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
        f"🤖 **کپچا**\n\n"
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
    
    if answer == correct:
        context.user_data["captcha_passed"] = True
        await query.answer("✅ درست بود!", show_alert=True)
        
        # ادامه ثبت‌نام
        keyboard = [
            [InlineKeyboardButton("🚀 ساخت کیف پول", callback_data="create_account")],
            [InlineKeyboardButton("📖 راهنمای ربات", callback_data="help")]
        ]
        await query.edit_message_text(
            f"✅ **کپچا تایید شد!**\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💎 به Mpyj Coin خوش اومدی\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🎁 یه اقتصاد سرگرمی بین دوستان\n"
            f"🪙 توکن اختصاصی برند Mpyj\n"
            f"🎲 شرط‌بندی و مسابقه\n\n"
            f"برای شروع، یه کیف پول برات می‌سازیم 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ اشتباه! دوباره تلاش کن", show_alert=True)