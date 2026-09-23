from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_user, set_character
from blockchain import get_balance, send_tokens_from_owner
from database import add_history
from config import OWNER_TELEGRAM_ID


CHARACTERS = {
    "warrior": {
        "name": "🗡️ جنگجو",
        "desc": "تو شرط‌بندی، ۵٪ جایزه بیشتر",
        "bonus": "bet_prize_5",
    },
    "wizard": {
        "name": "🧙 جادوگر",
        "desc": "تو تاس، ۱ بار شانس دوباره",
        "bonus": "dice_reroll",
    },
    "trader": {
        "name": "💰 تاجر",
        "desc": "تو تراکنش‌ها، ۲٪ تخفیف",
        "bonus": "send_discount_2",
    },
    "hunter": {
        "name": "🎯 شکارچی",
        "desc": "تو لاتاری، ۲ بلیط به جای ۱",
        "bonus": "lottery_double",
    },
    "guardian": {
        "name": "🛡️ محافظ",
        "desc": "تو باخت شرط، ۱۰٪ ضرر کمتر",
        "bonus": "bet_loss_reduce_10",
    },
}

CHANGE_COST = 500  # هزینه تغییر شخصیت


async def show_characters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست شخصیت‌ها"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start بزن!")
        return
    
    current = user.get("character")
    
    if current:
        # کاربر قبلاً شخصیت انتخاب کرده
        char = CHARACTERS.get(current, {})
        balance = get_balance(user["wallet_address"])
        
        keyboard = []
        if balance >= CHANGE_COST:
            keyboard.append([InlineKeyboardButton(
                f"🔄 تغییر شخصیت ({CHANGE_COST} MPYJ)",
                callback_data="char_change_confirm"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                f"🔒 تغییر شخصیت ({CHANGE_COST} MPYJ)",
                callback_data="char_no_money"
            )])
        keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
        
        await update.message.reply_text(
            f"🎭 شخصیت تو\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{char.get('name', 'نامشخص')}\n"
            f"💡 {char.get('desc', '')}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"💰 موجودی: {balance} MPYJ\n"
            f"💸 هزینه تغییر: {CHANGE_COST} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # کاربر شخصیت نداره → انتخاب
        text = "🎭 شخصیت‌ها\n\n━━━━━━━━━━━━━━━\n"
        text += "شخصیتت رو انتخاب کن:\n"
        text += "⚠️ بعد از انتخاب، فقط با پرداخت\n"
        text += f"💸 {CHANGE_COST} MPYJ قابل تغییره!\n"
        
        keyboard = []
        for char_id, char in CHARACTERS.items():
            keyboard.append([InlineKeyboardButton(
                f"{char['name']} — {char['desc']}",
                callback_data=f"char_{char_id}"
            )])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def choose_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب شخصیت (بار اول)"""
    query = update.callback_query
    await query.answer()
    
    char_id = query.data.replace("char_", "")
    user_id = query.from_user.id
    
    if char_id not in CHARACTERS:
        await query.edit_message_text("⚠️ شخصیت نامعتبر!")
        return
    
    user = get_user(user_id)
    if user and user.get("character"):
        await query.edit_message_text("⚠️ تو قبلاً شخصیت انتخاب کردی!")
        return
    
    char = CHARACTERS[char_id]
    
    keyboard = [[
        InlineKeyboardButton("✅ تایید", callback_data=f"char_confirm_{char_id}"),
        InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
    ]]
    
    await query.edit_message_text(
        f"🎭 تایید انتخاب\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{char['name']}\n"
        f"💡 {char['desc']}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚠️ بعد از تایید، فقط با\n"
        f"💸 {CHANGE_COST} MPYJ قابل تغییره!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید انتخاب شخصیت"""
    query = update.callback_query
    await query.answer()
    
    char_id = query.data.replace("char_confirm_", "")
    user_id = query.from_user.id
    
    if char_id not in CHARACTERS:
        await query.edit_message_text("⚠️ شخصیت نامعتبر!")
        return
    
    char = CHARACTERS[char_id]
    set_character(user_id, char_id)
    
    await query.edit_message_text(
        f"✅ شخصیت انتخاب شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{char['name']}\n"
        f"💡 {char['desc']}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🎉 مزیت از همین حالا فعاله!"
    )


async def change_character_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید تغییر شخصیت (با پرداخت)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user:
        await query.edit_message_text("⚠️ کاربر پیدا نشد!")
        return
    
    balance = get_balance(user["wallet_address"])
    
    if balance < CHANGE_COST:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n\n"
            f"💰 موجودی: {balance} MPYJ\n"
            f"💸 هزینه: {CHANGE_COST} MPYJ"
        )
        return
    
    keyboard = [[
        InlineKeyboardButton("✅ پرداخت و تغییر", callback_data="char_change_pay"),
        InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
    ]]
    
    await query.edit_message_text(
        f"⚠️ تایید پرداخت\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 هزینه تغییر: {CHANGE_COST} MPYJ\n"
        f"💳 موجودی فعلی: {balance} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"بعد از پرداخت، شخصیتت پاک میشه\n"
        f"و می‌تونی شخصیت جدید انتخاب کنی.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def change_character_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پرداخت هزینه تغییر شخصیت"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user:
        await query.edit_message_text("⚠️ کاربر پیدا نشد!")
        return
    
    balance = get_balance(user["wallet_address"])
    
    if balance < CHANGE_COST:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n💰 {balance} MPYJ"
        )
        return
    
    await query.edit_message_text("⏳ در حال پردازش...")
    
    # انتقال هزینه به Owner
    from config import OWNER_WALLET
    tx_hash, error = send_tokens_from_owner(OWNER_WALLET, CHANGE_COST)
    
    if error:
        await query.edit_message_text(f"❌ خطا: {error}")
        return
    
    # پاک کردن شخصیت
    set_character(user_id, None)
    add_history(user_id, OWNER_TELEGRAM_ID, CHANGE_COST, "character_change", tx_hash)
    
    # نشون دادن لیست شخصیت‌ها
    text = "🎭 شخصیت جدیدت رو انتخاب کن:\n\n━━━━━━━━━━━━━━━\n"
    
    keyboard = []
    for char_id, char in CHARACTERS.items():
        keyboard.append([InlineKeyboardButton(
            f"{char['name']} — {char['desc']}",
            callback_data=f"char_{char_id}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await query.edit_message_text(
        f"✅ پرداخت انجام شد!\n\n"
        f"💰 {CHANGE_COST} MPYJ کسر شد\n"
        f"🔗 {tx_hash[:30]}...\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🎭 حالا شخصیت جدیدت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def no_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پیام کمبود موجودی"""
    query = update.callback_query
    await query.answer("❌ موجودیت کافی نیست!", show_alert=True)