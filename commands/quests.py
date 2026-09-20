from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_user, has_done_quest_today, add_quest_completion,
    add_history
)
from blockchain import send_tokens_from_owner, get_balance


QUESTS = {
    "daily_login": {
        "name": "🌅 ورود روزانه",
        "reward": 10,
        "desc": "هر روز /start بزن"
    },
    "send_3": {
        "name": "📤 ۳ تراکنش",
        "reward": 30,
        "desc": "۳ بار سکه بفرست"
    },
    "balance_check": {
        "name": "💰 چک موجودی",
        "reward": 5,
        "desc": "موجودیت رو چک کن"
    },
}


async def show_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش ماموریت‌های روزانه"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start رو بزن!")
        return
    
    text = "🎯 ماموریت‌های روزانه\n\n━━━━━━━━━━━━━━━\n"
    
    keyboard = []
    for quest_id, quest in QUESTS.items():
        done = has_done_quest_today(user_id, quest_id)
        status = "✅" if done else "⏳"
        text += f"{status} {quest['name']}\n"
        text += f"     💰 جایزه: {quest['reward']} MPYJ\n"
        text += f"     📝 {quest['desc']}\n\n"
        
        if not done:
            keyboard.append([InlineKeyboardButton(
                f"🎯 {quest['name']}",
                callback_data=f"quest_do_{quest_id}"
            )])
    
    text += "━━━━━━━━━━━━━━━"
    
    if keyboard:
        keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text + "\n\n🎉 همه ماموریت‌های امروز رو انجام دادی!"
        )


async def do_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انجام یه ماموریت"""
    query = update.callback_query
    await query.answer()
    
    quest_id = query.data.replace("quest_do_", "")
    user_id = query.from_user.id
    
    quest = QUESTS.get(quest_id)
    if not quest:
        await query.edit_message_text("⚠️ ماموریت پیدا نشد!")
        return
    
    if has_done_quest_today(user_id, quest_id):
        await query.edit_message_text("⚠️ این ماموریت رو امروز انجام دادی!")
        return
    
    user = get_user(user_id)
    if not user:
        await query.edit_message_text("⚠️ اول /start بزن!")
        return
    
    await query.edit_message_text("⏳ در حال پرداخت جایزه...")
    
    tx_hash, error = send_tokens_from_owner(user["wallet_address"], quest["reward"])
    
    if error:
        await query.edit_message_text(f"❌ خطا: {error}")
        return
    
    add_quest_completion(user_id, quest_id)
    add_history(0, user_id, quest["reward"], "quest", tx_hash)
    
    await query.edit_message_text(
        f"✅ ماموریت انجام شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{quest['name']}\n"
        f"💰 جایزه: {quest['reward']} MPYJ\n"
        f"🔗 {tx_hash[:30]}...\n"
        f"━━━━━━━━━━━━━━━"
    )