from telegram import Update
from telegram.ext import ContextTypes
from database import get_history, get_user


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = get_history(user_id, limit=10)
    
    if not history:
        await update.message.reply_text(
            "📜 تاریخچه تراکنش‌ها\n\n"
            "━━━━━━━━━━━━━━━\n"
            "هنوز تراکنشی نداری!"
        )
        return
    
    text = "📜 تاریخچه تراکنش‌ها\n\n━━━━━━━━━━━━━━━\n"
    
    for h in history:
        from_id = h["from_id"]
        to_id = h["to_id"]
        amount = h["amount"]
        reason = h["reason"]
        created = str(h.get("created_at", ""))[:16]
        
        if from_id == user_id:
            icon = "📤"
            direction = "ارسال به"
            peer_id = to_id
        else:
            icon = "📥"
            direction = "دریافت از"
            peer_id = from_id
        
        peer = get_user(peer_id)
        if peer:
            peer_name = peer.get("first_name") or peer.get("username") or f"کاربر {peer_id}"
        else:
            peer_name = f"کاربر {peer_id}"
        
        reason_map = {
            "send": "انتقال",
            "reward": "جایزه",
            "admin_add": "افزایش توسط ادمین",
            "bet": "شرط‌بندی",
        }
        reason_fa = reason_map.get(reason, reason)
        
        text += f"{icon} {direction} {peer_name}\n"
        text += f"     💰 {amount} MPYJ\n"
        text += f"     🔖 {reason_fa}\n"
        text += f"     🕐 {created}\n\n"
    
    text += "━━━━━━━━━━━━━━━"
    await update.message.reply_text(text)