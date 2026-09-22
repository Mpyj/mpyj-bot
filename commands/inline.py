from telegram import (
    Update, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import ContextTypes
from database import get_user, get_all_users
from blockchain import get_balance
from commands.helpers import format_number


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل درخواست‌های Inline"""
    query = update.inline_query.query.strip().lower()
    user_id = update.effective_user.id
    
    # ==================== راهنما ====================
    if not query:
        results = [
            InlineQueryResultArticle(
                id="help_balance",
                title="💰 دیدن موجودی",
                description="موجودیت رو تو هر چتی نشون بده",
                input_message_content=InputTextMessageContent(
                    "💰 برای دیدن موجودی، روی دکمه زیر بزن 👇"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 نمایش موجودی", callback_data="inline_balance")]
                ])
            ),
            InlineQueryResultArticle(
                id="help_leaderboard",
                title="🏆 جدول رتبه‌ها",
                description="ببین کی ثروتمندترینه",
                input_message_content=InputTextMessageContent(
                    "🏆 جدول رتبه‌بندی Mpyj\n\nبرای دیدن، روی دکمه بزن 👇"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏆 نمایش رتبه‌ها", callback_data="inline_leaderboard")]
                ])
            ),
            InlineQueryResultArticle(
                id="help_bet",
                title="🎲 شرط‌بندی",
                description="راهنمای کامل شرط‌بندی",
                input_message_content=InputTextMessageContent(
                    "🎲 شرط‌بندی Mpyj\n\nبرای دیدن راهنما، روی دکمه بزن 👇"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 راهنمای کامل", callback_data="help_bet")]
                ])
            ),
            InlineQueryResultArticle(
                id="help_dice",
                title="🎲 بازی تاس",
                description="راهنمای کامل تاس",
                input_message_content=InputTextMessageContent(
                    "🎲 بازی تاس Mpyj\n\nبرای دیدن راهنما، روی دکمه بزن 👇"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 راهنمای کامل", callback_data="help_dice")]
                ])
            ),
        ]
        await update.inline_query.answer(results, cache_time=5)
        return
    
    # ==================== balance ====================
    if query == "balance":
        user = get_user(user_id)
        if not user:
            results = [InlineQueryResultArticle(
                id="no_user",
                title="⚠️ اول /start بزن!",
                description="برای ساخت کیف پول، ربات رو استارت کن",
                input_message_content=InputTextMessageContent(
                    "⚠️ هنوز ثبت‌نام نکردی!"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 شروع", url="https://t.me/crypppttttoooobot")]
                ])
            )]
        else:
            balance = get_balance(user["wallet_address"])
            name = user["first_name"] or user["username"] or "کاربر"
            
            if balance < 100:
                emoji = "🌱"
            elif balance < 500:
                emoji = "💪"
            elif balance < 1000:
                emoji = "🔥"
            else:
                emoji = "👑"
            
            results = [InlineQueryResultArticle(
                id="balance",
                title=f"💰 موجودی: {format_number(balance)} MPYJ",
                description=f"{name}",
                input_message_content=InputTextMessageContent(
                    f"💰 موجودی در Mpyj Coin\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👤 {name}\n"
                    f"{emoji} {format_number(balance)} MPYJ\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📍 {user['wallet_address']}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 بروزرسانی", callback_data="inline_balance")]
                ])
            )]
        
        await update.inline_query.answer(results, cache_time=5)
        return
    
    # ==================== leaderboard ====================
    if query in ["leaderboard", "top"]:
        users = get_all_users()
        balances = []
        for u in users:
            bal = get_balance(u["wallet_address"])
            name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
            balances.append((name, bal))
        
        balances.sort(key=lambda x: x[1], reverse=True)
        
        text = "🏆 جدول رتبه‌بندی Mpyj\n\n━━━━━━━━━━━━━━━\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, bal) in enumerate(balances[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} {name} → {format_number(bal)} MPYJ\n"
        
        results = [InlineQueryResultArticle(
            id="leaderboard",
            title="🏆 جدول رتبه‌بندی",
            description="۱۰ نفر برتر",
            input_message_content=InputTextMessageContent(text),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="inline_leaderboard")]
            ])
        )]
        
        await update.inline_query.answer(results, cache_time=5)
        return
    
    # ==================== پیش‌فرض ====================
    results = [InlineQueryResultArticle(
        id="default",
        title="❓ دستور نامعتبر",
        description="balance یا leaderboard",
        input_message_content=InputTextMessageContent(
            "❓ دستور نامعتبر!\n\n"
            "balance - موجودی\n"
            "leaderboard - رتبه‌ها"
        )
    )]
    await update.inline_query.answer(results, cache_time=5)