from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_all_users_except, get_user, create_dice_game,
    add_dice_player, get_dice_players, get_dice_game,
    update_dice_value, update_dice_game_status, add_history
)
from blockchain import get_balance, send_tokens_from_owner
from commands.helpers import format_number


DICE_EMOJIS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}


async def start_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع بازی تاس"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start بزن!")
        return
    
    # ساخت بازی جدید
    game_id = create_dice_game(user_id)
    context.user_data["dice_game_id"] = game_id
    context.user_data["dice_players"] = []
    
    # دکمه‌های انتخاب تعداد
    keyboard = [
        [
            InlineKeyboardButton("👥 ۲ نفر", callback_data=f"dice_count_2_{game_id}"),
            InlineKeyboardButton("👥 ۳ نفر", callback_data=f"dice_count_3_{game_id}"),
        ],
        [
            InlineKeyboardButton("👥 ۴ نفر", callback_data=f"dice_count_4_{game_id}"),
            InlineKeyboardButton("👥 ۵ نفر", callback_data=f"dice_count_5_{game_id}"),
        ],
        [
            InlineKeyboardButton("👥 ۶ نفر", callback_data=f"dice_count_6_{game_id}"),
        ],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await update.message.reply_text(
        "🎲 بازی تاس\n\n"
        "━━━━━━━━━━━━━━━\n"
        "چند نفر بازی می‌کنن؟\n\n"
        "💡 حداقل ۲، حداکثر ۶ نفر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب بازیکن‌ها"""
    query = update.callback_query
    await query.answer()
    
    # dice_count_2_123
    parts = query.data.replace("dice_count_", "").split("_")
    count = int(parts[0])
    game_id = int(parts[1])
    
    context.user_data["dice_count"] = count
    context.user_data["dice_game_id"] = game_id
    context.user_data["dice_players"] = [query.from_user.id]
    
    # لیست کاربرا
    users = get_all_users_except(query.from_user.id)
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"dice_add_{u['telegram_id']}_{game_id}"
        )])
    keyboard.append([InlineKeyboardButton("✅ شروع بازی", callback_data=f"dice_start_{game_id}")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await query.edit_message_text(
        f"🎲 بازی تاس\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 تعداد: {count} نفر\n"
        f"✅ انتخاب شده: ۱ نفر\n\n"
        f"بقیه بازیکن‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن بازیکن به بازی"""
    query = update.callback_query
    await query.answer()
    
    # dice_add_123_456
    parts = query.data.replace("dice_add_", "").split("_")
    player_id = int(parts[0])
    game_id = int(parts[1])
    
    players = context.user_data.get("dice_players", [])
    count = context.user_data.get("dice_count", 2)
    
    if player_id in players:
        await query.answer("⚠️ قبلاً اضافه شده!", show_alert=True)
        return
    
    if len(players) >= count:
        await query.answer(f"⚠️ حداکثر {count} نفر!", show_alert=True)
        return
    
    players.append(player_id)
    context.user_data["dice_players"] = players
    
    # نمایش لیست به‌روز
    users = get_all_users_except(query.from_user.id)
    
    keyboard = []
    for u in users[:15]:
        if u["telegram_id"] in players:
            continue
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"dice_add_{u['telegram_id']}_{game_id}"
        )])
    
    if len(players) >= count:
        keyboard.append([InlineKeyboardButton("✅ شروع بازی", callback_data=f"dice_start_{game_id}")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await query.edit_message_text(
        f"🎲 بازی تاس\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 تعداد: {count} نفر\n"
        f"✅ انتخاب شده: {len(players)} نفر\n\n"
        f"بقیه بازیکن‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع بازی — مقدار شرط رو بگیر"""
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.replace("dice_start_", ""))
    context.user_data["dice_step"] = "waiting_amount"
    context.user_data["dice_game_id"] = game_id
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
    
    await query.edit_message_text(
        "🎲 بازی تاس\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💰 مقدار شرط چقدره؟ (برای هر نفر)\n\n"
        "✏️ مقدار رو بنویس:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انداختن تاس (فقط ادمین) — یا خودکار"""
    from telegram import Update
    import random
    
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.replace("dice_roll_", ""))
    game = get_dice_game(game_id)
    players = get_dice_players(game_id)
    
    if not players:
        await query.edit_message_text("⚠️ بازیکنی نیست!")
        return
    
    # انداختن تاس برای هر بازیکن
    results = []
    for p in players:
        dice_value = random.randint(1, 6)
        update_dice_value(game_id, p["user_id"], dice_value)
        user = get_user(p["user_id"])
        name = user["first_name"] or user["username"] or "کاربر"
        results.append((name, dice_value))
    
    # پیدا کردن برنده
    max_dice = max(r[1] for r in results)
    winners = [r for r in results if r[1] == max_dice]
    
    text = "🎲 نتیجه تاس\n\n━━━━━━━━━━━━━━━\n"
    for name, dice in results:
        text += f"{DICE_EMOJIS[dice]} {name} → {dice}\n"
    text += "━━━━━━━━━━━━━━━\n\n"
    
    if len(winners) == 1:
        winner_name, _ = winners[0]
        text += f"🏆 برنده: {winner_name} (با عدد {max_dice})\n\n"
        text += "💰 جایزه به برنده واریز میشه..."
    else:
        text += f"⚠️ مساوی! {len(winners)} نفر با عدد {max_dice}\n"
        text += "ادمین تصمیم می‌گیره."
    
    await query.edit_message_text(text)


async def resolve_dice_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعیین برنده توسط ادمین (اگه مساوی شد یا خودکار نشد)"""
    # این تابع از پنل ادمین صدا زده میشه
    pass