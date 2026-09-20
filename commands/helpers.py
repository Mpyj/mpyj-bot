from telegram import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 موجودی", "📤 ارسال"],
        ["🎲 شرط‌بندی", "🏆 رتبه‌ها"],
        ["👤 پروفایل", "📜 تاریخچه"],
        ["❓ راهنما"],
    ],
    resize_keyboard=True
)

# منوی کاربری مخصوص ادمین (با دکمه برگشت)
ADMIN_MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 موجودی", "📤 ارسال"],
        ["🎲 شرط‌بندی", "🏆 رتبه‌ها"],
        ["👤 پروفایل", "📜 تاریخچه"],
        ["❓ راهنما"],
        ["👑 برگشت به پنل ادمین"],
    ],
    resize_keyboard=True
)

# منوی ادمین
ADMIN_MENU = ReplyKeyboardMarkup(
    [
        ["👥 کاربران", "➕ افزایش موجودی"],
        ["➖ کاهش موجودی", "📊 آمار"],
        ["🎁 جایزه", "📢 پیام همگانی"],
        ["👤 منوی کاربری"],
    ],
    resize_keyboard=True
)

def format_number(n):
    return f"{n:,}"