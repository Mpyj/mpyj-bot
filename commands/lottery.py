import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_user, buy_lottery_ticket, get_lottery_participants,
    get_week_number, add_history
)
from blockchain import send_tokens_from_owner, get_balance


LOTTERY_PRICE = 100  # قیمت بلیط


async def show_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش صفحه لاتاری"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start رو بزن!")
        return
    
    participants = get_lottery_participants()
    week = get_week_number()
    
    # چک کن کاربر بلیط داره یا نه
    has_ticket = any(p["user_id"] == user_id for p in participants)
    
    text = f"🎰 لاتاری هفتگی #{week}\n\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"👥 شرکت‌کننده‌ها: {len(participants)} نفر\n"
    text += f"💰 قیمت بلیط: {LOTTERY_PRICE} MPYJ\n"
    text += f"🎁 جایزه: {len(participants) * LOTTERY_PRICE} MPYJ\n"
    text += f"━━━━━━━━━━━━━━━\n\n"
    
    if has_ticket:
        text += "✅ تو این هفته بلیط داری!\n"
        text += "منتظر قرعه‌کشی باش..."
        await update.message.reply_text(text)
    else:
        text += "💡 با خرید بلیط، شانس بردن جایزه رو داری!"
        
        keyboard = [
            [InlineKeyboardButton(f"🎫 خرید بلیط ({LOTTERY_PRICE} MPYJ)", callback_data="lottery_buy")],
            [InlineKeyboardButton("❌ بستن", callback_data="cancel_all")]
        ]
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def buy_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خرید بلیط لاتاری"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = get_user(user_id)
    balance = get_balance(user["wallet_address"])
    
    if balance < LOTTERY_PRICE:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n\n"
            f"💰 موجودی: {balance} MPYJ\n"
            f"🎫 قیمت بلیط: {LOTTERY_PRICE} MPYJ"
        )
        return
    
    await query.edit_message_text("⏳ در حال خرید بلیط...")
    
    # کم کردن از موجودی کاربر (از Owner به Owner، پس فقط تو دیتابیس ثبت)
    # توجه: چون Owner پول رو می‌ده، ما فقط تو دیتابیس ثبت می‌کنیم
    # در واقع پول از موجودی Owner به خزانه لاتاری میره
    
    ticket_number, error = buy_lottery_ticket(user_id)
    
    if error:
        await query.edit_message_text(f"⚠️ {error}")
        return
    
    # کم کردن از کاربر و انتقال به خزانه (از Owner به Owner)
    # اینجا فقط تو دیتابیس ثبت میکنیم که کاربر بلیط خریده
    add_history(user_id, 0, LOTTERY_PRICE, "lottery_buy", "")
    
    await query.edit_message_text(
        f"🎉 بلیط خریداری شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎫 شماره بلیط: {ticket_number}\n"
        f"💰 پرداختی: {LOTTERY_PRICE} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🍀 موفق باشی!"
    )


async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قرعه‌کشی (فقط ادمین) - دستی"""
    if update.effective_user.id != int(os.getenv("OWNER_TELEGRAM_ID")):
        return
    
    participants = get_lottery_participants()
    if not participants:
        await update.message.reply_text("😴 هیچ شرکت‌کننده‌ای نیست!")
        return
    
    import random
    winner = random.choice(participants)
    winner_user = get_user(winner["user_id"])
    name = winner_user["first_name"] or winner_user["username"] or "ناشناس"
    
    prize = len(participants) * LOTTERY_PRICE
    
    await update.message.reply_text(
        f"🎰 قرعه‌کشی لاتاری\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎫 تعداد شرکت‌کننده: {len(participants)}\n"
        f"🎁 جایزه: {prize} MPYJ\n"
        f"🏆 برنده: {name}\n"
        f"🎫 شماره بلیط: {winner['ticket_number']}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"💡 از پنل ادمین، جایزه رو به برنده بده."
    )