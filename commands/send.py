from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_all_users_except, get_user
from blockchain import get_balance
from commands.helpers import format_number


async def start_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = get_all_users_except(user_id)
    
    if not users:
        await update.message.reply_text("😴 هنوز کاربر دیگه‌ای نیست!")
        return
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"send_to_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "📤 **به کی می‌خوای سکه بفرستی؟**\n\n"
        "━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def choose_send_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_id = int(query.data.replace("send_to_", ""))
    user_id = query.from_user.id
    context.user_data["send_target"] = target_id
    
    balance = get_balance(get_user(user_id)["wallet_address"])
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or f"کاربر {target_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("💵 ۱۰", callback_data="send_amt_10"),
            InlineKeyboardButton("💵 ۵۰", callback_data="send_amt_50"),
            InlineKeyboardButton("💵 ۱۰۰", callback_data="send_amt_100"),
        ],
        [
            InlineKeyboardButton("💎 ۵۰۰", callback_data="send_amt_500"),
            InlineKeyboardButton("💎 ۱۰۰۰", callback_data="send_amt_1000"),
        ],
        [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="send_amt_custom")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await query.edit_message_text(
        f"📤 **ارسال به {name}**\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 موجودی تو: **{format_number(balance)} MPYJ**\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"چقدر بفرستم؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )