from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_TELEGRAM_ID
from database import get_user, add_user
from blockchain import create_wallet, add_member_on_chain
from commands.helpers import MAIN_MENU, ADMIN_MENU


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = get_user(user.id)
    
    if existing:
        menu = ADMIN_MENU if user.id == OWNER_TELEGRAM_ID else MAIN_MENU
        role = "👑 ادمین" if user.id == OWNER_TELEGRAM_ID else "👤 کاربر"
        
        await update.message.reply_text(
            f"✨ سلام {user.first_name} عزیز!\n"
            f"🎭 نقش: {role}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💎 به Mpyj Coin خوش برگشتی\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"از منوی زیر انتخاب کن 👇",
            reply_markup=menu
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🚀 ساخت کیف پول", callback_data="create_account")],
            [InlineKeyboardButton("📖 راهنمای ربات", callback_data="help")]
        ]
        await update.message.reply_text(
            f"🌟 سلام {user.first_name} عزیز!\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💎 به Mpyj Coin خوش اومدی\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"🎁 یه اقتصاد سرگرمی بین دوستان\n"
            f"🪙 توکن اختصاصی برند Mpyj\n"
            f"🎲 شرط‌بندی و مسابقه\n\n"
            f"برای شروع، یه کیف پول برات می‌سازیم 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # ساخت کیف پول
    wallet = create_wallet()
    
    # اضافه کردن به دیتابیس
    success = add_user(
        user.id, user.username, user.first_name,
        wallet["address"], wallet["private_key"]
    )
    
    if not success:
        await query.edit_message_text("⚠️ قبلاً ثبت‌نام کردی!")
        return
    
    # ✅ اضافه کردن به عنوان عضو روی بلاک‌چین
    await query.edit_message_text("⏳ در حال ثبت نام روی بلاک‌چین...")
    
    tx_hash, error = add_member_on_chain(wallet["address"], 0)
    
    if error:
        await query.edit_message_text(
            f"⚠️ حساب ساخته شد ولی ثبت روی بلاک‌چین fail شد:\n\n{error}\n\n"
            f"از مالک بخواه دوباره تلاش کنه."
        )
    else:
        await query.edit_message_text(
            f"🎉 کیف پولت با موفقیت ساخته شد!\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 آدرس کیف پول:\n"
            f"{wallet['address']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 موجودی: ۰ MPYJ\n\n"
            f"💡 از مالک بخواه بهت سکه بده\n"
            f"🔗 {tx_hash[:30]}..."
        )
    
    menu = ADMIN_MENU if user.id == OWNER_TELEGRAM_ID else MAIN_MENU
    await context.bot.send_message(
        chat_id=user.id,
        text="✨ از منوی زیر استفاده کن:",
        reply_markup=menu
    )