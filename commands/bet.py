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
    """شروع شرط‌بندی"""
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


async def confirm_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید نهایی — ارسال درخواست به حریف"""
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data.get("bet_amount")
    target_id = context.user_data.get("bet_target")
    title = context.user_data.get("bet_title", "شرط")
    user_id = query.from_user.id
    
    if not amount or not target_id:
        await query.edit_message_text("❌ خطا! دوباره شروع کن.")
        return
    
    user = get_user(user_id)
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or "کاربر"
    user_name = user["first_name"] or user["username"] or "کاربر"
    
    # چک موجودی هر دو
    user_balance = get_balance(user["wallet_address"])
    target_balance = get_balance(target["wallet_address"])
    
    if user_balance < amount:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n💰 موجودی: {user_balance} MPYJ"
        )
        return
    
    if target_balance < amount:
        await query.edit_message_text(
            f"❌ موجودی {name} کافی نیست!\n💰 موجودی: {target_balance} MPYJ"
        )
        return
    
    # ذخیره اطلاعات تو context
    context.user_data["bet_amount"] = amount
    context.user_data["bet_title"] = title
    
    # ✅ ارسال درخواست به حریف
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"bet_accept_{user_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"bet_reject_{user_id}"),
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎲 درخواست شرط‌بندی\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 از: {user_name}\n"
                f"📝 {title}\n"
                f"💰 مقدار: {amount} MPYJ\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"قبول می‌کنی؟"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.edit_message_text(
            f"✅ درخواست شرط به {name} فرستاده شد!\n\n"
            f"⏳ منتظر تایید {name} باش..."
        )
        
        # ذخیره اطلاعات برای وقتی که حریف قبول کرد
        context.bot_data[f"bet_request_{user_id}"] = {
            "challenger_id": user_id,
            "challenger_name": user_name,
            "target_id": target_id,
            "target_name": name,
            "title": title,
            "amount": amount
        }
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ خطا در ارسال درخواست:\n\n{e}\n\n"
            f"احتمالاً {name} ربات رو بلاک کرده یا /start نزده."
        )
    
    context.user_data.clear()


async def accept_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قبول شرط توسط حریف"""
    query = update.callback_query
    await query.answer()
    
    challenger_id = int(query.data.replace("bet_accept_", ""))
    target_id = query.from_user.id
    
    # گرفتن اطلاعات از bot_data
    request = context.bot_data.get(f"bet_request_{challenger_id}")
    
    if not request:
        await query.edit_message_text("⚠️ این درخواست منقضی شده!")
        return
    
    if request["target_id"] != target_id:
        await query.edit_message_text("⚠️ این درخواست برای تو نیست!")
        return
    
    challenger = get_user(challenger_id)
    target = get_user(target_id)
    challenger_name = challenger["first_name"] or challenger["username"] or "کاربر"
    target_name = target["first_name"] or target["username"] or "کاربر"
    
    # ثبت شرط
    bet_id = create_bet(
        request["title"], challenger_id, target_id, request["amount"]
    )
    add_history(challenger_id, target_id, request["amount"], "bet_created", "")
    
    # دکمه‌های تعیین برنده (برای ادمین)
    keyboard = [
        [
            InlineKeyboardButton(
                f"🏆 {challenger_name}",
                callback_data=f"settle_{bet_id}_1"
            ),
            InlineKeyboardButton(
                f"🏆 {target_name}",
                callback_data=f"settle_{bet_id}_2"
            ),
        ]
    ]
    
    await query.edit_message_text(
        f"✅ شرط قبول شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 شماره: #{bet_id}\n"
        f"📝 {request['title']}\n"
        f"👤 {challenger_name} vs {target_name}\n"
        f"💰 مقدار: {request['amount']} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚖️ ادمین، برنده رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # اطلاع به چلنجر
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=(
                f"✅ {target_name} شرط رو قبول کرد!\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🎯 شرط #{bet_id}\n"
                f"📝 {request['title']}\n"
                f"💰 مقدار: {request['amount']} MPYJ\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"⏳ منتظر تعیین برنده توسط ادمین باش..."
            )
        )
    except:
        pass
    
    # پاک کردن درخواست
    context.bot_data.pop(f"bet_request_{challenger_id}", None)


async def reject_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد شرط توسط حریف"""
    query = update.callback_query
    await query.answer()
    
    challenger_id = int(query.data.replace("bet_reject_", ""))
    target_id = query.from_user.id
    
    request = context.bot_data.get(f"bet_request_{challenger_id}")
    
    if not request:
        await query.edit_message_text("⚠️ این درخواست منقضی شده!")
        return
    
    target = get_user(target_id)
    target_name = target["first_name"] or target["username"] or "کاربر"
    
    await query.edit_message_text(
        f"❌ شرط رد شد.\n\n"
        f"📝 {request['title']}\n"
        f"💰 {request['amount']} MPYJ"
    )
    
    # اطلاع به چلنجر
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=(
                f"❌ {target_name} شرط رو رد کرد.\n\n"
                f"📝 {request['title']}\n"
                f"💰 {request['amount']} MPYJ"
            )
        )
    except:
        pass
    
    context.bot_data.pop(f"bet_request_{challenger_id}", None)


async def settle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعیین برنده شرط (فقط ادمین)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != OWNER_TELEGRAM_ID:
        await query.answer("⛔ فقط ادمین!", show_alert=True)
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
    
    tx_hash, error = send_tokens_from_owner(winner["wallet_address"], prize)
    
    if error:
        await query.edit_message_text(f"❌ خطا در پرداخت:\n\n{error}")
        return
    
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
    
    # اطلاع به برنده و بازنده
    try:
        await context.bot.send_message(
            chat_id=winner_id,
            text=f"🏆 تبریک! شرط #{bet_id} رو بردی!\n💰 {prize} MPYJ بهت اضافه شد."
        )
    except:
        pass
    
    try:
        await context.bot.send_message(
            chat_id=loser_id,
            text=f"💔 متاسفانه شرط #{bet_id} رو باختی.\n💰 {bet['amount']} MPYJ از دست دادی."
        )
    except:
        pass