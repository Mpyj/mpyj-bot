from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_TELEGRAM_ID
from database import (
    get_all_users, get_user, get_all_pending_rewards,
    get_pending_reward, update_pending_reward_status, add_history
)
from blockchain import (
    get_balance, get_owner_eth_balance, get_owner_token_balance,
    reward_winner, send_tokens_from_owner
)
from commands.helpers import format_number, ADMIN_MENU


def is_owner(user_id):
    return user_id == OWNER_TELEGRAM_ID


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ فقط مالک!")
        return
    
    await update.message.reply_text(
        "👑 پنل ادمین Mpyj\n\n"
        "━━━━━━━━━━━━━━━\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=ADMIN_MENU
    )


async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    text = f"👥 لیست کاربران ({len(users)} نفر)\n\n━━━━━━━━━━━━━━━\n"
    for u in users[:30]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        bal = get_balance(u["wallet_address"])
        text += f"👤 {name}\n     💰 {format_number(bal)} MPYJ\n"
        text += f"     🆔 {u['telegram_id']}\n\n"
    
    await update.message.reply_text(text)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    total_users = len(users)
    
    await update.message.reply_text("⏳ در حال محاسبه...")
    
    total_coins = 0
    richest = None
    max_bal = 0
    for u in users:
        bal = get_balance(u["wallet_address"])
        total_coins += bal
        if bal > max_bal:
            max_bal = bal
            richest = u
    
    eth_bal = get_owner_eth_balance()
    token_bal = get_owner_token_balance()
    pending = get_all_pending_rewards()
    
    text = f"📊 آمار کلی Mpyj\n\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"👥 کاربران: {total_users}\n"
    text += f"💰 مجموع سکه: {format_number(total_coins)} MPYJ\n"
    if richest:
        name = richest["first_name"] or richest["username"] or "ناشناس"
        text += f"👑 ثروتمندترین: {name} ({format_number(max_bal)})\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"⛽ ETH Owner: {eth_bal:.4f}\n"
    text += f"🪙 MPYJ Owner: {format_number(token_bal)}\n"
    text += f"🎁 جوایز در انتظار: {len(pending)}\n"
    text += f"━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(text)


async def show_pending_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جوایز در انتظار تایید (فقط ادمین)"""
    if not is_owner(update.effective_user.id):
        return
    
    rewards = get_all_pending_rewards()
    
    if not rewards:
        await update.message.reply_text(
            "🎁 جوایز در انتظار\n\n"
            "━━━━━━━━━━━━━━━\n"
            "هیچ جایزه‌ای در انتظار تایید نیست!"
        )
        return
    
    text = f"🎁 جوایز در انتظار ({len(rewards)} مورد)\n\n━━━━━━━━━━━━━━━\n"
    
    keyboard = []
    for r in rewards[:10]:
        user = get_user(r["user_id"])
        name = user["first_name"] or user["username"] or f"کاربر {r['user_id']}"
        
        text += f"🆔 #{r['id']}\n"
        text += f"👤 {name}\n"
        text += f"💰 {r['amount']} MPYJ\n"
        text += f"🔖 {r['reason']}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✅ تایید #{r['id']}", callback_data=f"approve_reward_{r['id']}"),
            InlineKeyboardButton(f"❌ رد #{r['id']}", callback_data=f"reject_reward_{r['id']}"),
        ])
    
    text += "━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع جایزه دادن به برنده"""
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"🎁 {name}",
            callback_data=f"reward_to_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "🎁 به کی جایزه بدم؟\n\n"
        "━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_reward_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_id = int(query.data.replace("reward_to_", ""))
    context.user_data["reward_target"] = target_id
    
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or f"کاربر {target_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 ۵۰", callback_data="reward_amt_50"),
            InlineKeyboardButton("🎁 ۱۰۰", callback_data="reward_amt_100"),
            InlineKeyboardButton("🎁 ۵۰۰", callback_data="reward_amt_500"),
        ],
        [
            InlineKeyboardButton("🏆 ۱۰۰۰", callback_data="reward_amt_1000"),
            InlineKeyboardButton("🏆 ۵۰۰۰", callback_data="reward_amt_5000"),
        ],
        [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="reward_amt_custom")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await query.edit_message_text(
        f"🎁 جایزه به {name}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"چقدر جایزه بدم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"➕ {name}",
            callback_data=f"admin_add_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "➕ به کی سکه بدم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"➖ {name}",
            callback_data=f"admin_remove_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "➖ از کی سکه کم کنم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    context.user_data["broadcast_mode"] = True
    await update.message.reply_text(
        "📢 پیام همگانی\n\n"
        "متن پیام رو بنویس:\n"
        "(یا /cancel بزن)"
    )