from telegram import Update
from telegram.ext import ContextTypes
from database import get_history, get_user
from commands.helpers import format_number


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = get_history(user_id, limit=10)
    
    if not history:
        await update.message.reply_text("📜 هنوز تراکنشی نداری!")
        return
    
    text = "📜 **تاریخچه تراکنش‌ها**\n\n━━━━━━━━━━━━━━━\n"
    
    for h in history:
        from_id = h["from_id"]
        to_id = h["to_id"]
        amount = h["amount"]
        reason = h["reason"]
        
        if from_id == user_id:
            icon = "📤"
            direction = "ارسال به"
            peer = get_user(to_id)
        else:
            icon = "📥"
            direction = "دریافت از"
            peer = get_user(from_id)
        
        peer_name = "ناشناس"
        if peer:
            peer_name = peer["first_name"] or peer["username"] or f"کاربر {peer['telegram_id']}"
        
        text += f"{icon} {direction} **{peer_name}**\n"
        text += f"     💰 {format_number(amount)} MPYJ\n"
        text += f"     🔖 {reason}\n\n"
    
    text += "━━━━━━━━━━━━━━━"
    await update.message.reply_text(text, parse_mode="Markdown")