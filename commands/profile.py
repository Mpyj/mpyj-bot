from telegram import Update
from telegram.ext import ContextTypes
from database import get_user
from blockchain import get_balance
from commands.helpers import format_number


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ اول /start رو بزن!")
        return
    
    balance = get_balance(user["wallet_address"])
    name = user["first_name"] or "بی‌نام"
    username = f"@{user['username']}" if user["username"] else "نداری"
    
    await update.message.reply_text(
        f"👤 پروفایل تو\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 نام: {name}\n"
        f"🆔 یوزرنیم: {username}\n"
        f"🔢 آیدی: {user['telegram_id']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 موجودی: {format_number(balance)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📍 آدرس کیف پول:\n{user['wallet_address']}"
    )