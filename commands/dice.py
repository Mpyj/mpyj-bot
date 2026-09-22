from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_user, get_all_users_except, create_dice_game,
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
    
    context.user_data.clear()
    
    keyboard = [
        [
            InlineKeyboardButton("👥 ۲ نفر", callback_data="dice_count_2"),
            InlineKeyboardButton("👥 ۳ نفر", callback_data="dice_count_3"),
        ],
        [
            InlineKeyboardButton("👥 ۴ نفر", callback_data="dice_count_4"),
            InlineKeyboardButton("👥 ۵ نفر", callback_data="dice_count_5"),
        ],
        [
            InlineKeyboardButton("👥 ۶ نفر", callback_data="dice_count_6"),
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


async def choose_dice_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب تعداد بازیکن‌ها"""
    query = update.callback_query
    await query.answer()
    
    count = int(query.data.replace("dice_count_", ""))
    user_id = query.from_user.id
    
    context.user_data["dice_count"] = count
    context.user_data["dice_players"] = [user_id]
    
    # ساخت بازی تو دیتابیس
    game_id = create_dice_game(user_id)
    context.user_data["dice_game_id"] = game_id
    add_dice_player(game_id, user_id, 0)
    
    # لیست کاربران برای انتخاب
    users = get_all_users_except(user_id)
    
    if not users:
        await query.edit_message_text("😴 کاربر دیگه‌ای نیست!")
        return
    
    keyboard = []
    for u in users[:20]:
        if u["telegram_id"] in context.user_data["dice_players"]:
            continue
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"dice_add_{u['telegram_id']}"
        )])
    
    if len(context.user_data["dice_players"]) >= count:
        keyboard.append([InlineKeyboardButton("✅ ادامه", callback_data="dice_next")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await query.edit_message_text(
        f"🎲 بازی تاس\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 تعداد: {count} نفر\n"
        f"✅ انتخاب شده: {len(context.user_data['dice_players'])} نفر\n\n"
        f"بقیه بازیکن‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_dice_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن بازیکن به بازی"""
    query = update.callback_query
    await query.answer()
    
    player_id = int(query.data.replace("dice_add_", ""))
    user_id = query.from_user.id
    count = context.user_data.get("dice_count", 2)
    game_id = context.user_data.get("dice_game_id")
    players = context.user_data.get("dice_players", [])
    
    if player_id in players:
        await query.answer("⚠️ قبلاً اضافه شده!", show_alert=True)
        return
    
    if len(players) >= count:
        await query.answer(f"⚠️ حداکثر {count} نفر!", show_alert=True)
        return
    
    players.append(player_id)
    context.user_data["dice_players"] = players
    add_dice_player(game_id, player_id, 0)
    
    # لیست به‌روز
    users = get_all_users_except(user_id)
    
    keyboard = []
    for u in users[:20]:
        if u["telegram_id"] in players:
            continue
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"dice_add_{u['telegram_id']}"
        )])
    
    if len(players) >= count:
        keyboard.append([InlineKeyboardButton("✅ ادامه", callback_data="dice_next")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await query.edit_message_text(
        f"🎲 بازی تاس\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 تعداد: {count} نفر\n"
        f"✅ انتخاب شده: {len(players)} نفر\n\n"
        f"بقیه بازیکن‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dice_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بعد از انتخاب بازیکن‌ها، مقدار شرط رو بگیر"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["dice_step"] = "waiting_amount"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
    
    await query.edit_message_text(
        "🎲 مقدار شرط\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💰 هر نفر چقدر شرط بذاره؟\n\n"
        "✏️ عدد رو بنویس:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def create_dice_message(update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
    """ساخت پیام تاس تو چت"""
    user_id = update.effective_user.id
    players = context.user_data.get("dice_players", [])
    game_id = context.user_data.get("dice_game_id")
    
    # ذخیره مقدار
    for p in players:
        from database import get_conn, PLACEHOLDER, USE_POSTGRES
        conn = get_conn()
        c = conn.cursor()
        c.execute(f"""
            UPDATE dice_players SET bet_amount = {PLACEHOLDER}
            WHERE game_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER}
        """, (amount, game_id, p))
        conn.commit()
        c.close()
        conn.close()
    
    # ساخت لیست نام‌ها
    names = []
    for p in players:
        u = get_user(p)
        name = u["first_name"] or u["username"] or f"کاربر {p}"
        names.append(name)
    
    names_text = "\n".join([f"  👤 {n}" for n in names])
    total = amount * len(players)
    
    keyboard = [
        [InlineKeyboardButton("🎲 انداختن تاس", callback_data=f"dice_roll_{game_id}")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await update.message.reply_text(
        f"🎲 بازی تاس\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 بازیکن‌ها ({len(players)} نفر):\n{names_text}\n\n"
        f"💰 شرط هر نفر: {format_number(amount)} MPYJ\n"
        f"🏆 مجموع جایزه: {format_number(total)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🎯 سازنده، دکمه تاس رو بزن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["dice_amount"] = amount
    context.user_data["dice_step"] = None


async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انداختن تاس برای همه بازیکن‌ها"""
    import random
    
    query = update.callback_query
    await query.answer()
    
    game_id = int(query.data.replace("dice_roll_", ""))
    user_id = query.from_user.id
    
    game = get_dice_game(game_id)
    if not game:
        await query.edit_message_text("⚠️ بازی پیدا نشد!")
        return
    
    if game["status"] != "waiting":
        await query.edit_message_text("⚠️ این بازی قبلاً تموم شده!")
        return
    
    # فقط سازنده می‌تونه تاس بندازه
    if game["creator_id"] != user_id:
        await query.answer("⛔ فقط سازنده بازی!", show_alert=True)
        return
    
    players = get_dice_players(game_id)
    if len(players) < 2:
        await query.edit_message_text("⚠️ حداقل ۲ بازیکن لازمه!")
        return
    
    # چک موجودی همه
    for p in players:
        user = get_user(p["user_id"])
        balance = get_balance(user["wallet_address"])
        if balance < p["bet_amount"]:
            name = user["first_name"] or user["username"] or "کاربر"
            await query.edit_message_text(
                f"❌ موجودی {name} کافی نیست!\n"
                f"💰 {balance} MPYJ < {p['bet_amount']} MPYJ"
            )
            return
    
    # انداختن تاس برای هر نفر
    results = []
    for p in players:
        dice_value = random.randint(1, 6)
        update_dice_value(game_id, p["user_id"], dice_value)
        user = get_user(p["user_id"])
        name = user["first_name"] or user["username"] or "کاربر"
        results.append({
            "user_id": p["user_id"],
            "name": name,
            "dice": dice_value,
            "bet": p["bet_amount"],
            "wallet": user["wallet_address"]
        })
    
    # پیدا کردن برنده
    max_dice = max(r["dice"] for r in results)
    winners = [r for r in results if r["dice"] == max_dice]
    
    text = "🎲 نتیجه تاس\n\n━━━━━━━━━━━━━━━\n"
    for r in results:
        text += f"{DICE_EMOJIS[r['dice']]} {r['name']} → {r['dice']}\n"
    text += "━━━━━━━━━━━━━━━\n\n"
    
    if len(winners) == 1:
        # برنده مشخصه
        winner = winners[0]
        total_prize = sum(r["bet"] for r in results)
        
        text += f"🏆 برنده: {winner['name']} (عدد {max_dice})\n\n"
        text += "⏳ در حال پرداخت جایزه..."
        
        await query.edit_message_text(text)
        
        # ارسال جایزه
        tx_hash, error = send_tokens_from_owner(winner["wallet"], total_prize)
        
        if error:
            await query.edit_message_text(
                text + f"\n\n❌ خطا در پرداخت: {error}"
            )
            return
        
        update_dice_game_status(game_id, "finished", winner["user_id"], max_dice)
        add_history(0, winner["user_id"], total_prize, "dice_won", tx_hash)
        
        await query.edit_message_text(
            f"🎲 نتیجه تاس\n\n"
            f"━━━━━━━━━━━━━━━\n" +
            "".join([f"{DICE_EMOJIS[r['dice']]} {r['name']} → {r['dice']}\n" for r in results]) +
            f"━━━━━━━━━━━━━━━\n\n"
            f"🏆 برنده: {winner['name']} (عدد {max_dice})\n"
            f"💰 جایزه: {format_number(total_prize)} MPYJ\n"
            f"🔗 {tx_hash[:30]}..."
        )
    else:
        # مساوی
        names = " و ".join([w["name"] for w in winners])
        text += f"⚠️ مساوی! {len(winners)} نفر با عدد {max_dice}:\n{names}\n\n"
        text += "⚖️ ادمین باید برنده رو انتخاب کنه."
        
        update_dice_game_status(game_id, "finished", None, max_dice)
        
        # دکمه‌های انتخاب برنده برای ادمین
        keyboard = []
        for w in winners:
            keyboard.append([InlineKeyboardButton(
                f"🏆 {w['name']}",
                callback_data=f"dice_winner_{game_id}_{w['user_id']}"
            )])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def dice_settle_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعیین برنده تاس توسط ادمین (تو مساوی)"""
    from config import OWNER_TELEGRAM_ID
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != OWNER_TELEGRAM_ID:
        await query.answer("⛔ فقط ادمین!", show_alert=True)
        return
    
    # dice_winner_{game_id}_{winner_id}
    parts = query.data.replace("dice_winner_", "").split("_")
    game_id = int(parts[0])
    winner_id = int(parts[1])
    
    players = get_dice_players(game_id)
    winner = None
    for p in players:
        if p["user_id"] == winner_id:
            winner = p
            break
    
    if not winner:
        await query.edit_message_text("⚠️ برنده پیدا نشد!")
        return
    
    winner_user = get_user(winner_id)
    winner_name = winner_user["first_name"] or winner_user["username"] or "کاربر"
    total_prize = sum(p["bet_amount"] for p in players)
    
    await query.edit_message_text("⏳ در حال پرداخت جایزه...")
    
    tx_hash, error = send_tokens_from_owner(
        winner_user["wallet_address"], total_prize
    )
    
    if error:
        await query.edit_message_text(f"❌ خطا: {error}")
        return
    
    update_dice_game_status(game_id, "settled", winner_id)
    add_history(0, winner_id, total_prize, "dice_won", tx_hash)
    
    await query.edit_message_text(
        f"✅ برنده تعیین شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 {winner_name}\n"
        f"💰 جایزه: {format_number(total_prize)} MPYJ\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 {tx_hash[:30]}..."
    )