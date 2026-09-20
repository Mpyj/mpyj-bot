from telegram import Update
from telegram.ext import ContextTypes
from database import get_all_users
from blockchain import get_balance
from commands.helpers import format_number


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    await update.message.reply_text("⏳ در حال محاسبه رتبه‌ها...")
    
    # گرفتن موجودی همه
    balances = []
    for u in users:
        bal = get_balance(u["wallet_address"])
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        balances.append((name, bal))
    
    balances.sort(key=lambda x: x[1], reverse=True)
    
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 **جدول رتبه‌بندی**\n\n━━━━━━━━━━━━━━━\n"
    
    for i, (name, bal) in enumerate(balances[:10]):
        if i < 3:
            medal = medals[i]
        else:
            medal = f"  {i+1}."
        text += f"{medal} {name}\n     💰 {format_number(bal)} MPYJ\n\n"
    
    text += "━━━━━━━━━━━━━━━"
    await update.message.reply_text(text, parse_mode="Markdown")