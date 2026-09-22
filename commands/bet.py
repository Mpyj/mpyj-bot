from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_all_users_except, get_user, create_bet,
    add_history, get_bet, update_bet_status, get_pending_bets
)
from blockchain import get_balance, send_tokens_from_owner
from commands.helpers import format_number
from config import OWNER_TELEGRAM_ID


async def start_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع شرط‌بندی — تو پیوی یا گروه"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text(
            "⚠️ اول باید تو پیوی ربات /start بزنی!\n\n"
            "👉 @crypppttttoooobot"
        )
        return
    
    users = get_all_users_except(user_id)
    
    if not users:
        await update.message.reply_text("😴 هنوز کاربر دیگه‌ای نیست!")
        return
    
    context.user_data.clear()
    context.user_data["bet_step"] = "choose_opponent"
    context.user_data["bet_chat_id"] = update.effective_chat.id
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"🎯 {name}",
            callback_data=f"bet_with_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "🎲 شرط‌بندی\n\n"
        "━━━━━━━━━━━━━━━\n"
        "با کی می‌خوای شرط ببندی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بعد از انتخاب حریف، عنوان رو بگیر"""
    query = update.callback_query
    await query.answer()
    
    target_id = int(query.data.replace("bet_with_", ""))
    context.user_data["bet_target"] = target_id
    context.user_data["bet_step"] = "waiting_title"
    
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or "کاربر"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
    
    await query.edit_message_text(
        f"🎲 شرط با {name}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 عنوان شرط چیه؟\n\n"
        f"مثال: بازی فیفا امشب\n"
        f"✏️ عنوان رو بنویس:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_bet_amounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بعد از گرفتن عنوان، مقدار رو نشون بده"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    balance = get_balance(get_user(user_id)["wallet_address"])
    target = get_user(context.user_data["bet_target"])
    name = target["first_name"] or target["username"] or "کاربر"
    title = context.user_data.get("bet_title", "")
    
    keyboard = [
        [
            InlineKeyboardButton("💵 ۱۰", callback_data="bet_amt_10"),
            InlineKeyboardButton("💵 ۵۰", callback_data="bet_amt_50"),
            InlineKeyboardButton("💵 ۱۰۰", callback_data="bet_amt_100"),
        ],
        [
            InlineKeyboardButton("💎 ۵۰۰", callback_data="bet_amt_500"),
            InlineKeyboardButton("💎 ۱۰۰۰", callback_data="bet_amt_1000"),
        ],
        [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="bet_amt_custom")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await query.edit_message_text(
        f"🎲 شرط با {name}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 {title}\n"
        f"💰 موجودی تو: {format_number(balance)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"چقدر شرط می‌بندی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید نهایی شرط"""
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data.get("bet_amount")
    target_id = context.user_data.get("bet_target")
    title = context.user_data.get("bet_title", "شرط")
    
    if not amount or not target_id:
        await query.edit_message_text("❌ خطا! دوباره شروع کن.")
        return
    
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or "کاربر"
    
    keyboard = [[
        InlineKeyboardButton("✅ ثبت شرط", callback_data="bet_do_confirm"),
        InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
    ]]
    
    await query.edit_message_text(
        f"🎲 تایید شرط\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 {title}\n"
        f"👤 حریف: {name}\n"
        f"💰 مقدار: {amount} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚠️ {amount} MPYJ از موجودی تو قفل میشه!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def execute_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای شرط — تو همون چت (پیوی یا گروه)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    target_id = context.user_data.get("bet_target")
    amount = context.user_data.get("bet_amount")
    title = context.user_data.get("bet_title", "شرط")
    
    if not target_id or not amount:
        await query.edit_message_text("❌ خطا! دوباره شروع کن.")
        return
    
    user = get_user(user_id)
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or "کاربر"
    user_name = user["first_name"] or user["username"] or "بازیکن ۱"
    
    await query.edit_message_text("⏳ در حال ثبت شرط...")
    
    # چک موجودی هر دو طرف
    user_balance = get_balance(user["wallet_address"])
    target_balance = get_balance(target["wallet_address"])
    
    if user_balance < amount:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n💰 موجودی: {user_balance} MPYJ"
        )
        context.user_data.clear()
        return
    
    if target_balance < amount:
        await query.edit_message_text(
            f"❌ موجودی {name} کافی نیست!\n💰 موجودی: {target_balance} MPYJ"
        )
        context.user_data.clear()
        return
    
    # ثبت شرط تو دیتابیس
    bet_id = create_bet(title, user_id, target_id, amount)
    add_history(user_id, target_id, amount, "bet_created", "")
    
    # پیام نهایی با دکمه تعیین برنده
    keyboard = [
        [
            InlineKeyboardButton(
                f"🏆 {user_name}",
                callback_data=f"settle_{bet_id}_1"
            ),
            InlineKeyboardButton(
                f"🏆 {name}",
                callback_data=f"settle_{bet_id}_2"
            ),
        ]
    ]
    
    await query.edit_message_text(
        f"✅ شرط ثبت شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 شماره: #{bet_id}\n"
        f"📝 {title}\n"
        f"👤 {user_name} vs {name}\n"
        f"💰 مقدار: {amount} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚖️ ادمین، برنده رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.clear()


async def settle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعیین برنده شرط (تو چت یا گروه)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # فقط ادمین
    if user_id != OWNER_TELEGRAM_ID:
        await query.answer("⛔ فقط ادمین می‌تونه برنده رو تعیین کنه!", show_alert=True)
        return
    
    parts = query.data.replace("settle_", "").split("_")
    bet_id = int(parts[0])
    winner_choice = int(parts[1])
    
    bet = get_bet(bet_id)
    
    if not bet:
        await query.edit_message_text("⚠️ شرط پیدا نشد!")
        return
    
    if bet["status"] != "pending":
        await query.edit_message_text("⚠️ این شرط قبلاً تعیین شده!")
        return
    
    winner_id = bet["player1_id"] if winner_choice == 1 else bet["player2_id"]
    loser_id = bet["player2_id"] if winner_choice == 1 else bet["player1_id"]
    
    winner = get_user(winner_id)
    loser = get_user(loser_id)
    winner_name = winner["first_name"] or winner["username"] or "کاربر"
    loser_name = loser["first_name"] or loser["username"] or "کاربر"
    
    await query.edit_message_text("⏳ در حال پرداخت جایزه...")
    
    prize = bet["amount"] * 2
    
    # ارسال جایزه به برنده
    tx_hash, error = send_tokens_from_owner(winner["wallet_address"], prize)
    
    if error:
        await query.edit_message_text(
            f"❌ خطا در پرداخت:\n\n{error}\n\n"
            f"🆔 #{bet_id}"
        )
        return
    
    # آپدیت دیتابیس
    update_bet_status(bet_id, "settled", winner_id)
    add_history(0, winner_id, prize, "bet_won", tx_hash)
    
    await query.edit_message_text(
        f"✅ شرط تعیین شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 شرط #{bet_id}\n"
        f"📝 {bet['title']}\n"
        f"🏆 برنده: {winner_name}\n"
        f"💔 باخت: {loser_name}\n"
        f"💰 جایزه: {format_number(prize)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 {tx_hash[:30]}..."
    )