from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, InlineQueryHandler, filters, ContextTypes
)
from config import TELEGRAM_TOKEN, OWNER_TELEGRAM_ID
from database import (
    init_db, get_user, get_all_users, get_user_by_username,
    add_history, create_bet, get_pending_reward,
    update_pending_reward_status, needs_captcha,
    claim_user_nft
)
from blockchain import get_balance, send_tokens_from_owner, reward_winner
from commands.helpers import MAIN_MENU, ADMIN_MENU, ADMIN_MAIN_MENU, format_number
from commands.start import start, create_account
from commands.captcha import send_captcha, verify_captcha
from commands.balance import show_balance
from commands.profile import show_profile
from commands.leaderboard import show_leaderboard
from commands.help import show_help
from commands.history import show_history
from commands.send import start_send, choose_send_amount
from commands.bet import (
    start_bet, start_bet_from_callback, choose_bet_amount,
    confirm_bet, execute_bet, settle_bet,
    accept_bet, reject_bet
)
from commands.dice import (
    start_dice, start_dice_from_callback, choose_dice_count,
    add_player_to_dice, dice_next, create_dice_message,
    roll_dice, dice_settle_winner
)
from commands.characters import (
    show_characters, choose_character, confirm_character,
    change_character_confirm, change_character_pay, no_money
)
from commands.clans import (
    show_clans_menu, start_create_clan, create_clan_handler,
    view_invite, accept_invite, reject_invite,
    invite_member, send_invite, show_members,
    leave_clan, delete_clan_handler, show_clan_leaderboard
)
from commands.nfts import show_nfts, claim_nft_handler, show_my_nfts
from commands.quests import show_quests, do_quest
from commands.lottery import show_lottery, buy_ticket
from commands.inline import inline_query
from commands.admin import (
    show_admin_panel, show_users, show_stats,
    start_reward, choose_reward_amount,
    start_add_balance, start_remove_balance, start_broadcast,
    show_pending_rewards, show_pending_bets,
    manage_nfts, create_default_nfts, set_nft_command, handle_nft_photo
)


def is_owner(user_id):
    return user_id == OWNER_TELEGRAM_ID


# ==================== هندل دکمه‌های Inline ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    # ✅ چک کپچا (به جز دکمه‌های کپچا و create_account)
    if not data.startswith("captcha_") and data != "create_account":
        user = get_user(user_id)
        if user and needs_captcha(user_id):
            await query.answer("⏱️ کپچا لازمه! /start رو بزن", show_alert=True)
            return
    
    # ==================== کپچا ====================
    if data.startswith("captcha_"):
        await verify_captcha(update, context)
        return
    
    # ==================== ثبت‌نام ====================
    elif data == "create_account":
        await create_account(update, context)
        return
    
    # ==================== راهنما ====================
    elif data == "help":
        try:
            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start")]]
            await query.edit_message_text(
                "📖 راهنمای Mpyj Coin\n\n"
                "━━━━━━━━━━━━━━━\n"
                "💰 موجودی — دیدن سکه‌هات\n"
                "📤 ارسال — فرستادن سکه\n"
                "🎲 شرط‌بندی — شرط با دوستان\n"
                "🎲 تاس — بازی تاس\n"
                "🎭 شخصیت — انتخاب شخصیت\n"
                "🏰 کلن — ساخت کلن\n"
                "🎨 NFT — جوایز ویژه\n"
                "🏆 رتبه‌ها — جدول امتیازات\n"
                "🎯 ماموریت‌ها — انجام ماموریت\n"
                "🎰 لاتاری — شانس بردن جایزه\n"
                "👤 پروفایل — اطلاعات حساب\n"
                "📜 تاریخچه — تراکنش‌های اخیر\n"
                "━━━━━━━━━━━━━━━",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            await context.bot.send_message(
                chat_id=user_id,
                text="📖 راهنما: از منو استفاده کن"
            )
        return
    
    # ==================== راهنمای شرط‌بندی ====================
    elif data == "help_bet":
        keyboard = [
            [InlineKeyboardButton("🎲 شروع شرط‌بندی", callback_data="start_bet_from_help")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start")],
        ]
        await query.edit_message_text(
            "📖 راهنمای شرط‌بندی\n\n"
            "━━━━━━━━━━━━━━━\n"
            "1️⃣ /bet بزن\n"
            "2️⃣ حریفت رو انتخاب کن\n"
            "3️⃣ عنوان شرط رو بنویس\n"
            "4️⃣ مقدار شرط رو انتخاب کن\n"
            "5️⃣ تایید کن\n\n"
            "📩 ربات به حریفت پیام میده\n"
            "🏆 ادمین برنده رو انتخاب می‌کنه\n"
            "💰 جایزه: ۲ برابر مقدار شرط",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # ==================== راهنمای تاس ====================
    elif data == "help_dice":
        keyboard = [
            [InlineKeyboardButton("🎲 شروع تاس", callback_data="start_dice_from_help")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start")],
        ]
        await query.edit_message_text(
            "📖 راهنمای تاس\n\n"
            "━━━━━━━━━━━━━━━\n"
            "1️⃣ /dice بزن\n"
            "2️⃣ تعداد بازیکن‌ها\n"
            "3️⃣ بازیکن‌ها رو انتخاب کن\n"
            "4️⃣ مقدار شرط\n"
            "5️⃣ دکمه تاس\n\n"
            "🏆 هر کی عدد بالاتر بیاره، برنده‌ست",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # ==================== شروع از راهنما ====================
    elif data == "start_bet_from_help":
        await start_bet_from_callback(update, context)
        return
    
    elif data == "start_dice_from_help":
        await start_dice_from_callback(update, context)
        return
    
    # ==================== برگشت ====================
    elif data == "back_to_start":
        user = query.from_user
        existing = get_user(user.id)
        if existing:
            menu = ADMIN_MAIN_MENU if is_owner(user.id) else MAIN_MENU
            await query.edit_message_text(f"✨ سلام {user.first_name} عزیز!")
            await context.bot.send_message(chat_id=user.id, text="منو:", reply_markup=menu)
        return
    
    # ==================== لغو ====================
    elif data == "cancel_all":
        context.user_data.clear()
        menu = ADMIN_MAIN_MENU if is_owner(user_id) else MAIN_MENU
        await query.edit_message_text("❌ لغو شد.")
        await context.bot.send_message(chat_id=user_id, text="منو:", reply_markup=menu)
        return
    
    # ==================== Inline: موجودی ====================
    elif data == "inline_balance":
        user = get_user(user_id)
        if not user:
            await query.edit_message_text("⚠️ اول /start بزن!")
            return
        balance = get_balance(user["wallet_address"])
        name = user["first_name"] or user["username"] or "کاربر"
        await query.edit_message_text(
            f"💰 موجودی در Mpyj Coin\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 {name}\n"
            f"💰 {format_number(balance)} MPYJ\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 {user['wallet_address'][:10]}...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="inline_balance")]
            ])
        )
        return
    
    # ==================== Inline: رتبه‌ها ====================
    elif data == "inline_leaderboard":
        users = get_all_users()
        balances = []
        for u in users:
            bal = get_balance(u["wallet_address"])
            name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
            balances.append((name, bal))
        balances.sort(key=lambda x: x[1], reverse=True)
        text = "🏆 جدول رتبه‌بندی\n\n━━━━━━━━━━━━━━━\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, bal) in enumerate(balances[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} {name} → {format_number(bal)} MPYJ\n"
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="inline_leaderboard")]
            ])
        )
        return
    
    # ==================== شخصیت ====================
    elif data.startswith("char_confirm_"):
        await confirm_character(update, context)
        return
    elif data == "char_change_confirm":
        await change_character_confirm(update, context)
        return
    elif data == "char_change_pay":
        await change_character_pay(update, context)
        return
    elif data == "char_no_money":
        await no_money(update, context)
        return
    elif data.startswith("char_"):
        await choose_character(update, context)
        return
    
    # ==================== کلن ====================
    elif data == "clan_create":
        await start_create_clan(update, context)
        return
    elif data.startswith("clan_view_invite_"):
        await view_invite(update, context)
        return
    elif data.startswith("clan_accept_"):
        await accept_invite(update, context)
        return
    elif data.startswith("clan_reject_"):
        await reject_invite(update, context)
        return
    elif data.startswith("clan_members_"):
        await show_members(update, context)
        return
    elif data.startswith("clan_invite_to_"):
        await send_invite(update, context)
        return
    elif data.startswith("clan_invite_"):
        await invite_member(update, context)
        return
    elif data.startswith("clan_leave_"):
        await leave_clan(update, context)
        return
    elif data.startswith("clan_delete_"):
        await delete_clan_handler(update, context)
        return
    elif data == "clan_leaderboard":
        await show_clan_leaderboard(update, context)
        return
    
    # ==================== NFT ====================
    elif data.startswith("nft_claim_"):
        await claim_nft_handler(update, context)
        return
    elif data == "nft_create_defaults":
        await create_default_nfts(update, context)
        return
    elif data.startswith("claim_special_config_"):
        parts = data.replace("claim_special_config_", "").split("_")
        nft_id = int(parts[0])
        claim_user_nft(nft_id)
        await query.edit_message_text(f"✅ کانفیگ تحویل داده شد!\n🆔 NFT #{nft_id}")
        return
    elif data.startswith("claim_special_programming_"):
        parts = data.replace("claim_special_programming_", "").split("_")
        nft_id = int(parts[0])
        claim_user_nft(nft_id)
        await query.edit_message_text(f"✅ سفارش برنامه‌نویسی ثبت شد!\n🆔 NFT #{nft_id}")
        return
    
    # ==================== تاس ====================
    elif data.startswith("dice_count_"):
        await choose_dice_count(update, context)
        return
    elif data.startswith("dice_add_"):
        await add_player_to_dice(update, context)
        return
    elif data == "dice_next":
        await dice_next(update, context)
        return
    elif data.startswith("dice_roll_"):
        await roll_dice(update, context)
        return
    elif data.startswith("dice_winner_"):
        await dice_settle_winner(update, context)
        return
    
    # ==================== ماموریت ====================
    elif data.startswith("quest_do_"):
        await do_quest(update, context)
        return
    
    # ==================== لاتاری ====================
    elif data == "lottery_buy":
        await buy_ticket(update, context)
        return
    
    # ==================== ارسال ====================
    elif data.startswith("send_to_"):
        await choose_send_amount(update, context)
        return
    elif data.startswith("send_amt_"):
        if data == "send_amt_custom":
            context.user_data["waiting_custom_amount"] = "send"
            await query.edit_message_text("✏️ مقدار دلخواه رو بنویس:")
            return
        amount = int(data.replace("send_amt_", ""))
        context.user_data["send_amount"] = amount
        target_id = context.user_data["send_target"]
        target = get_user(target_id)
        name = target["first_name"] or target["username"] or "کاربر"
        keyboard = [[
            InlineKeyboardButton("✅ تایید", callback_data="send_confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
        ]]
        await query.edit_message_text(
            f"📤 تایید ارسال\n\n👤 به: {name}\n💰 {amount} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    elif data == "send_confirm":
        target_id = context.user_data.get("send_target")
        amount = context.user_data.get("send_amount")
        target = get_user(target_id)
        await query.edit_message_text("⏳ در حال ارسال...")
        tx_hash, error = send_tokens_from_owner(target["wallet_address"], amount)
        if error:
            await query.edit_message_text(f"❌ خطا: {error}")
        else:
            name = target["first_name"] or target["username"] or "کاربر"
            add_history(user_id, target_id, amount, "send", tx_hash)
            await query.edit_message_text(f"✅ {amount} MPYJ به {name} فرستاده شد!\n🔗 {tx_hash[:30]}...")
        context.user_data.clear()
        return
    
    # ==================== شرط‌بندی ====================
    elif data.startswith("bet_with_"):
        await choose_bet_amount(update, context)
        return
    elif data.startswith("bet_amt_"):
        if data == "bet_amt_custom":
            context.user_data["waiting_custom_amount"] = "bet"
            await query.edit_message_text("✏️ مقدار دلخواه رو بنویس:")
            return
        amount = int(data.replace("bet_amt_", ""))
        context.user_data["bet_amount"] = amount
        await confirm_bet(update, context)
        return
    elif data == "bet_do_confirm":
        await execute_bet(update, context)
        return
    elif data.startswith("bet_accept_"):
        await accept_bet(update, context)
        return
    elif data.startswith("bet_reject_"):
        await reject_bet(update, context)
        return
    elif data.startswith("settle_"):
        await settle_bet(update, context)
        return
    
    # ==================== ادمین: جایزه ====================
    elif data.startswith("reward_to_"):
        await choose_reward_amount(update, context)
        return
    elif data.startswith("reward_amt_"):
        if data == "reward_amt_custom":
            context.user_data["waiting_custom_amount"] = "reward"
            await query.edit_message_text("✏️ مقدار جایزه رو بنویس:")
            return
        amount = int(data.replace("reward_amt_", ""))
        context.user_data["reward_amount"] = amount
        target_id = context.user_data["reward_target"]
        target = get_user(target_id)
        name = target["first_name"] or target["username"] or "کاربر"
        keyboard = [[
            InlineKeyboardButton("🎁 ثبت", callback_data="reward_confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
        ]]
        await query.edit_message_text(
            f"🎁 تایید جایزه\n👤 {name}\n💰 {amount} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    elif data == "reward_confirm":
        target_id = context.user_data.get("reward_target")
        amount = context.user_data.get("reward_amount")
        target = get_user(target_id)
        await query.edit_message_text("⏳ در حال ثبت...")
        tx_hash, error = reward_winner(target["wallet_address"], amount, "Reward")
        if error:
            await query.edit_message_text(f"❌ خطا: {error}")
        else:
            name = target["first_name"] or target["username"] or "کاربر"
            add_history(OWNER_TELEGRAM_ID, target_id, amount, "reward", tx_hash)
            await query.edit_message_text(f"🎁 جایزه ثبت شد!\n👤 {name}\n💰 {amount} MPYJ")
        context.user_data.clear()
        return
    
    # ==================== ادمین: تایید/رد جایزه ====================
    elif data.startswith("approve_reward_"):
        reward_id = int(data.replace("approve_reward_", ""))
        reward = get_pending_reward(reward_id)
        if not reward or reward["status"] != "pending":
            await query.edit_message_text("⚠️ قبلاً پردازش شده!")
            return
        user = get_user(reward["user_id"])
        name = user["first_name"] or user["username"] or "کاربر"
        await query.edit_message_text(f"⏳ در حال ارسال...")
        tx_hash, error = send_tokens_from_owner(user["wallet_address"], reward["amount"])
        if error:
            await query.edit_message_text(f"❌ {error}")
        else:
            update_pending_reward_status(reward_id, "approved")
            add_history(OWNER_TELEGRAM_ID, reward["user_id"], reward["amount"], "reward", tx_hash)
            await query.edit_message_text(f"✅ {reward['amount']} MPYJ به {name} پرداخت شد!")
        return
    elif data.startswith("reject_reward_"):
        reward_id = int(data.replace("reject_reward_", ""))
        update_pending_reward_status(reward_id, "rejected")
        await query.edit_message_text(f"❌ جایزه #{reward_id} رد شد.")
        return
    
    # ==================== ادمین: افزایش/کاهش ====================
    elif data.startswith("admin_add_"):
        target_id = int(data.replace("admin_add_", ""))
        context.user_data["admin_action"] = "add"
        context.user_data["admin_target"] = target_id
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
        await query.edit_message_text("➕ مقدار رو بنویس:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data.startswith("admin_remove_"):
        target_id = int(data.replace("admin_remove_", ""))
        context.user_data["admin_action"] = "remove"
        context.user_data["admin_target"] = target_id
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
        await query.edit_message_text("➖ مقدار رو بنویس:", reply_markup=InlineKeyboardMarkup(keyboard))
        return


# ==================== هندل پیام‌های متنی ====================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    # تو گروه‌ها فقط دستورات
    if chat_type in ["group", "supergroup"]:
        if not text.startswith("/"):
            return
        if not any(cmd in text for cmd in ["/start", "/bet", "/dice", "/admin", "/cancel"]):
            return
    
    # چک کپچا
    if not text.startswith("/start"):
        user = get_user(user_id)
        if user and needs_captcha(user_id):
            await update.message.reply_text("⏱️ کپچا لازمه! /start بزن.")
            return
    
    # آپلود عکس NFT (ادمین)
    if is_owner(user_id) and context.user_data.get("setnft_type"):
        if update.message.photo:
            await handle_nft_photo(update, context)
            return
    
    # انتظار اسم کلن
    if context.user_data.get("clan_step") == "waiting_name":
        await create_clan_handler(update, context, text)
        return
    
    # انتظار مقدار تاس
    if context.user_data.get("dice_step") == "waiting_amount":
        try:
            amount = int(text)
        except:
            await update.message.reply_text("⚠️ عدد بفرست!")
            return
        if amount <= 0:
            await update.message.reply_text("⚠️ عدد باید بزرگتر از صفر باشه!")
            return
        await create_dice_message(update, context, amount)
        return
    
    # انتظار عنوان شرط
    if context.user_data.get("bet_step") == "waiting_title":
        context.user_data["bet_title"] = text
        context.user_data["bet_step"] = None
        balance = get_balance(get_user(user_id)["wallet_address"])
        target = get_user(context.user_data["bet_target"])
        name = target["first_name"] or target["username"] or "کاربر"
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
        await update.message.reply_text(
            f"🎲 شرط با {name}\n📝 {text}\n💰 {format_number(balance)} MPYJ\n\nچقدر شرط می‌بندی؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # انتظار مقدار دلخواه
    if "waiting_custom_amount" in context.user_data:
        try:
            amount = int(text)
        except:
            await update.message.reply_text("⚠️ عدد بفرست!")
            return
        if amount <= 0:
            await update.message.reply_text("⚠️ عدد باید بزرگتر از صفر باشه!")
            return
        mode = context.user_data["waiting_custom_amount"]
        context.user_data.pop("waiting_custom_amount")
        if mode == "send":
            context.user_data["send_amount"] = amount
            target = get_user(context.user_data["send_target"])
            name = target["first_name"] or target["username"] or "کاربر"
            keyboard = [[
                InlineKeyboardButton("✅ تایید", callback_data="send_confirm"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
            ]]
            await update.message.reply_text(f"📤 تایید ارسال به {name}\n💰 {amount} MPYJ", reply_markup=InlineKeyboardMarkup(keyboard))
        elif mode == "bet":
            context.user_data["bet_amount"] = amount
            await confirm_bet(update, context)
        elif mode == "reward":
            context.user_data["reward_amount"] = amount
            target = get_user(context.user_data["reward_target"])
            name = target["first_name"] or target["username"] or "کاربر"
            keyboard = [[
                InlineKeyboardButton("🎁 ثبت", callback_data="reward_confirm"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
            ]]
            await update.message.reply_text(f"🎁 تایید جایزه به {name}\n💰 {amount} MPYJ", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # انتظار مقدار ادمین
    if is_owner(user_id) and "admin_action" in context.user_data:
        try:
            amount = int(text)
        except:
            await update.message.reply_text("⚠️ عدد بفرست!")
            return
        action = context.user_data["admin_action"]
        target_id = context.user_data["admin_target"]
        target = get_user(target_id)
        name = target["first_name"] or target["username"] or "کاربر"
        await update.message.reply_text("⏳ در حال ثبت...")
        if action == "add":
            tx_hash, error = send_tokens_from_owner(target["wallet_address"], amount)
            if error:
                await update.message.reply_text(f"❌ {error}", reply_markup=ADMIN_MENU)
            else:
                add_history(OWNER_TELEGRAM_ID, target_id, amount, "admin_add", tx_hash)
                await update.message.reply_text(f"✅ {amount} MPYJ به {name} اضافه شد!", reply_markup=ADMIN_MENU)
        context.user_data.clear()
        return
    
    # پیام همگانی
    if is_owner(user_id) and context.user_data.get("broadcast_mode"):
        context.user_data.pop("broadcast_mode")
        users = get_all_users()
        sent = 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u["telegram_id"], text=f"📢 پیام از ادمین\n\n{text}")
                sent += 1
            except:
                pass
        await update.message.reply_text(f"✅ به {sent} نفر ارسال شد!", reply_markup=ADMIN_MENU)
        return
    
    # سوییچ منو
    if is_owner(user_id) and text == "👤 منوی کاربری":
        await update.message.reply_text("👤 منوی کاربری:", reply_markup=ADMIN_MAIN_MENU)
        return
    if is_owner(user_id) and text == "👑 برگشت به پنل ادمین":
        await update.message.reply_text("👑 پنل ادمین:", reply_markup=ADMIN_MENU)
        return
    
    # منوی ادمین
    if is_owner(user_id):
        if text == "👥 کاربران":
            await show_users(update, context)
            return
        elif text == "➕ افزایش موجودی":
            await start_add_balance(update, context)
            return
        elif text == "➖ کاهش موجودی":
            await start_remove_balance(update, context)
            return
        elif text == "📊 آمار":
            await show_stats(update, context)
            return
        elif text == "🎁 جایزه":
            await start_reward(update, context)
            return
        elif text == "📢 پیام همگانی":
            await start_broadcast(update, context)
            return
        elif text == "🎯 جوایز در انتظار":
            await show_pending_rewards(update, context)
            return
        elif text == "🎲 شرط‌های در انتظار":
            await show_pending_bets(update, context)
            return
        elif text == "🎨 مدیریت NFT":
            await manage_nfts(update, context)
            return
    
    # منوی کاربری
    if text == "💰 موجودی":
        await show_balance(update, context)
    elif text == "📤 ارسال":
        await start_send(update, context)
    elif text == "🎲 شرط‌بندی":
        await start_bet(update, context)
    elif text == "🎲 تاس":
        await start_dice(update, context)
    elif text == "🎭 شخصیت":
        await show_characters(update, context)
    elif text == "🏰 کلن":
        await show_clans_menu(update, context)
    elif text == "🎨 NFT ها":
        await show_nfts(update, context)
    elif text == "🏆 رتبه‌ها":
        await show_leaderboard(update, context)
    elif text == "🎯 ماموریت‌ها":
        await show_quests(update, context)
    elif text == "🎰 لاتاری":
        await show_lottery(update, context)
    elif text == "👤 پروفایل":
        await show_profile(update, context)
    elif text == "📜 تاریخچه":
        await show_history(update, context)
    elif text == "❓ راهنما":
        await show_help(update, context)
    else:
        await update.message.reply_text("❓ از منو انتخاب کن یا /help بزن.")


# ==================== /admin و /cancel ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_admin_panel(update, context)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    menu = ADMIN_MAIN_MENU if is_owner(update.effective_user.id) else MAIN_MENU
    await update.message.reply_text("❌ لغو شد.", reply_markup=menu)


# ==================== main ====================
def main():
    init_db()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("bet", start_bet))
    app.add_handler(CommandHandler("dice", start_dice))
    app.add_handler(CommandHandler("setnft", set_nft_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.PHOTO, message_handler))
    
    print("🤖 ربات Mpyj روشن شد!")
    print(f"👑 Owner ID: {OWNER_TELEGRAM_ID}")
    app.run_polling()


if __name__ == "__main__":
    main()