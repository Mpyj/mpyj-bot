from telegram import Update
from telegram.ext import ContextTypes


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **راهنمای Mpyj Coin**\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💎 **دستورات کاربری**\n"
        "━━━━━━━━━━━━━━━\n"
        "💰 **موجودی** — دیدن سکه‌هات\n"
        "📤 **ارسال** — فرستادن سکه\n"
        "🎲 **شرط‌بندی** — شرط با دوستان\n"
        "🏆 **رتبه‌ها** — جدول امتیازات\n"
        "👤 **پروفایل** — اطلاعات حساب\n"
        "📜 **تاریخچه** — تراکنش‌های اخیر\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 **نکته**\n"
        "همه تراکنش‌ها روی بلاک‌چین\n"
        "Sepolia ثبت میشن ✅",
        parse_mode="Markdown"
    )