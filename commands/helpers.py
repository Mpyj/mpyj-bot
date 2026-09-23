from telegram import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 موجودی", "📤 ارسال"],
        ["🎲 شرط‌بندی", "🏆 رتبه‌ها"],
        ["🎯 ماموریت‌ها", "🎰 لاتاری"],
        ["🎲 تاس", "🎭 شخصیت"],
        ["🏰 کلن", "🎨 NFT ها"],
        ["👤 پروفایل", "📜 تاریخچه"],
        ["❓ راهنما"],
    ],
    resize_keyboard=True
)

ADMIN_MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 موجودی", "📤 ارسال"],
        ["🎲 شرط‌بندی", "🏆 رتبه‌ها"],
        ["🎯 ماموریت‌ها", "🎰 لاتاری"],
        ["🎲 تاس", "🎭 شخصیت"],
        ["🏰 کلن", "🎨 NFT ها"],
        ["👤 پروفایل", "📜 تاریخچه"],
        ["❓ راهنما"],
        ["👑 برگشت به پنل ادمین"],
    ],
    resize_keyboard=True
)

ADMIN_MENU = ReplyKeyboardMarkup(
    [
        ["👥 کاربران", "➕ افزایش موجودی"],
        ["➖ کاهش موجودی", "📊 آمار"],
        ["🎁 جایزه", "🎯 جوایز در انتظار"],
        ["🎲 شرط‌های در انتظار", "🎨 مدیریت NFT"],
        ["🖼️ آپلود عکس NFT", "📢 پیام همگانی"],
        ["👤 منوی کاربری"],
    ],
    resize_keyboard=True
)

def format_number(n):
    return f"{n:,}"