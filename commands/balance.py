from telegram import Update
from telegram.ext import ContextTypes
from database import get_user
from blockchain import get_balance
from commands.helpers import format_number


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ اول /start رو بزن!")
        return
    
    await update.message.reply_text("⏳ در حال دریافت از بلاک‌چین...")
    
    # ✅ از آدرس کیف پول خود کاربر می‌خونیم (نه از Owner)
    balance = get_balance(user["wallet_address"])
    
    if balance == 0:
        emoji = "🥺"
        msg = "هنوز سکه‌ای نداری!"
    elif balance < 100:
        emoji = "🌱"
        msg = "تازه شروع کردی!"
    elif balance < 1000:
        emoji = "💪"
        msg = "داری پیشرفت می‌کنی!"
    elif balance < 5000:
        emoji = "🔥"
        msg = "آتیشی!"
    else:
        emoji = "👑"
        msg = "پادشاهی!"
    
    await update.message.reply_text(
        f"💰 موجودی تو\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{emoji} {format_number(balance)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💬 {msg}\n\n"
        f"📍 آدرس: {user['wallet_address'][:10]}...{user['wallet_address'][-6:]}"
    )