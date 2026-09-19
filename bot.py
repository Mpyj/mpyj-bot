from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from config import TELEGRAM_TOKEN, OWNER_TELEGRAM_ID
from database import (
    init_db, get_user, add_user, get_all_users, get_user_by_username,
    get_balance, update_balance, transfer, get_history,
    get_all_users_except, add_history, create_bet
)

# ========== کیبوردها ==========
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 موجودی", "📤 ارسال"],
        ["🎲 شرط‌بندی", "🏆 رتبه‌ها"],
        ["👤 پروفایل", "❓ راهنما"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

ADMIN_MENU = ReplyKeyboardMarkup(
    [
        ["👥 لیست کاربران", "➕ افزایش موجودی"],
        ["➖ کاهش موجودی", "📊 آمار کلی"],
        ["📢 پیام همگانی", "👤 منوی کاربری"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = get_user(user.id)
    
    if existing:
        if user.id == OWNER_TELEGRAM_ID:
            await update.message.reply_text(
                f"سلام {user.first_name} 👋 (ادمین)\n"
                f"از منوی زیر انتخاب کن:",
                reply_markup=ADMIN_MENU
            )
        else:
            await update.message.reply_text(
                f"سلام {user.first_name} 👋\nخوش برگشتی!",
                reply_markup=MAIN_MENU
            )
    else:
        keyboard = [
            [InlineKeyboardButton("🚀 ساخت حساب", callback_data="create_account")],
            [InlineKeyboardButton("📖 راهنمای ربات", callback_data="help")]
        ]
        await update.message.reply_text(
            f"سلام {user.first_name} 👋\n"
            f"به ربات Mpyj Coin خوش اومدی!\n\n"
            f"برای شروع، یه حساب برات می‌سازیم:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ========== /admin ==========
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_TELEGRAM_ID:
        await update.message.reply_text("❌ فقط مالک!")
        return
    
    await update.message.reply_text(
        "👑 پنل ادمین\n\nاز منو انتخاب کن:",
        reply_markup=ADMIN_MENU
    )

# ========== هندل دکمه‌های Inline ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    user_id = user.id
    
    # ==================== ثبت‌نام ====================
    if data == "create_account":
        success = add_user(user.id, user.username, user.first_name)
        if success:
            await query.edit_message_text(
                f"✅ حسابت ساخته شد!\n\n"
                f"💰 موجودی اولیه: 0 MPYJ\n"
                f"(از مالک بخواه بهت سکه بده)"
            )
            menu = ADMIN_MENU if user.id == OWNER_TELEGRAM_ID else MAIN_MENU
            await context.bot.send_message(
                chat_id=user.id,
                text="از منوی زیر استفاده کن:",
                reply_markup=menu
            )
        else:
            await query.edit_message_text("❌ قبلاً ثبت‌نام کردی!")
    
    elif data == "help":
        await query.edit_message_text(
            "📖 راهنمای Mpyj Coin\n\n"
            "💰 موجودی - دیدن سکه‌هات\n"
            "📤 ارسال - فرستادن سکه\n"
            "🎲 شرط‌بندی - شرط بستن\n"
            "🏆 رتبه‌ها - جدول\n"
            "👤 پروفایل - اطلاعات حساب"
        )
    
    # ==================== لغو عمومی ====================
    elif data == "cancel_all":
        context.user_data.clear()
        menu = ADMIN_MENU if user_id == OWNER_TELEGRAM_ID else MAIN_MENU
        await query.edit_message_text("❌ لغو شد.")
        await context.bot.send_message(
            chat_id=user_id,
            text="منو:",
            reply_markup=menu
        )
        return
    
    # ==================== 📤 ارسال سکه ====================
    elif data.startswith("send_to_"):
        target_id = int(data.replace("send_to_", ""))
        target = get_user(target_id)
        if not target:
            await query.edit_message_text("❌ کاربر پیدا نشد!")
            return
        
        context.user_data["send_target"] = target_id
        balance = get_balance(user_id)
        name = target[2] or target[1] or f"کاربر {target_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("۱۰", callback_data="send_amt_10"),
                InlineKeyboardButton("۵۰", callback_data="send_amt_50"),
                InlineKeyboardButton("۱۰۰", callback_data="send_amt_100"),
            ],
            [
                InlineKeyboardButton("۵۰۰", callback_data="send_amt_500"),
                InlineKeyboardButton("۱۰۰۰", callback_data="send_amt_1000"),
            ],
            [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="send_amt_custom")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
        ]
        
        await query.edit_message_text(
            f"📤 چقدر به {name} بفرستم؟\n\n"
            f"💰 موجودی تو: {balance} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("send_amt_"):
        if data == "send_amt_custom":
            context.user_data["waiting_custom_amount"] = "send"
            await query.edit_message_text(
                "✏️ مقدار دلخواه رو بنویس و بفرست:\n(یا /cancel بزن)"
            )
            return
        
        amount = int(data.replace("send_amt_", ""))
        target_id = context.user_data.get("send_target")
        if not target_id:
            await query.edit_message_text("❌ دوباره شروع کن!")
            return
        
        target = get_user(target_id)
        name = target[2] or target[1] or f"کاربر {target_id}"
        balance = get_balance(user_id)
        
        if balance < amount:
            await query.edit_message_text(
                f"❌ موجودیت کافی نیست!\n"
                f"💰 موجودی: {balance}\n"
                f"📤 می‌خوای بفرستی: {amount}"
            )
            return
        
        context.user_data["send_amount"] = amount
        
        keyboard = [
            [
                InlineKeyboardButton("✅ تایید", callback_data="send_confirm"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
            ]
        ]
        
        await query.edit_message_text(
            f"📤 تایید نهایی:\n\n"
            f"به: {name}\n"
            f"مقدار: {amount} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "send_confirm":
        target_id = context.user_data.get("send_target")
        amount = context.user_data.get("send_amount")
        
        if not target_id or not amount:
            await query.edit_message_text("❌ دوباره شروع کن!")
            return
        
        success, msg = transfer(user_id, target_id, amount, "send")
        if success:
            target = get_user(target_id)
            name = target[2] or target[1] or f"کاربر {target_id}"
            new_balance = get_balance(user_id)
            await query.edit_message_text(
                f"✅ {amount} MPYJ به {name} فرستاده شد!\n\n"
                f"💰 موجودی جدید تو: {new_balance} MPYJ"
            )
        else:
            await query.edit_message_text(f"❌ {msg}")
        
        context.user_data.pop("send_target", None)
        context.user_data.pop("send_amount", None)
    
    # ==================== 🎲 شرط‌بندی ====================
    elif data.startswith("bet_with_"):
        target_id = int(data.replace("bet_with_", ""))
        target = get_user(target_id)
        if not target:
            await query.edit_message_text("❌ کاربر پیدا نشد!")
            return
        
        context.user_data["bet_target"] = target_id
        balance = get_balance(user_id)
        name = target[2] or target[1] or f"کاربر {target_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("۱۰", callback_data="bet_amt_10"),
                InlineKeyboardButton("۵۰", callback_data="bet_amt_50"),
                InlineKeyboardButton("۱۰۰", callback_data="bet_amt_100"),
            ],
            [
                InlineKeyboardButton("۵۰۰", callback_data="bet_amt_500"),
                InlineKeyboardButton("۱۰۰۰", callback_data="bet_amt_1000"),
            ],
            [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="bet_amt_custom")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
        ]
        
        await query.edit_message_text(
            f"🎲 چقدر با {name} شرط می‌بندی؟\n\n"
            f"💰 موجودی تو: {balance} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("bet_amt_"):
        if data == "bet_amt_custom":
            context.user_data["waiting_custom_amount"] = "bet"
            await query.edit_message_text(
                "✏️ مقدار دلخواه رو بنویس و بفرست:\n(یا /cancel بزن)"
            )
            return
        
        amount = int(data.replace("bet_amt_", ""))
        target_id = context.user_data.get("bet_target")
        if not target_id:
            await query.edit_message_text("❌ دوباره شروع کن!")
            return
        
        target = get_user(target_id)
        name = target[2] or target[1] or f"کاربر {target_id}"
        balance = get_balance(user_id)
        target_balance = get_balance(target_id)
        
        if balance < amount:
            await query.edit_message_text(
                f"❌ موجودیت کافی نیست!\n"
                f"💰 موجودی: {balance}\n"
                f"🎲 می‌خوای شرط ببندی: {amount}"
            )
            return
        
        if target_balance < amount:
            await query.edit_message_text(
                f"❌ موجودی {name} کافی نیست!\n"
                f"💰 موجودی {name}: {target_balance}"
            )
            return
        
        context.user_data["bet_amount"] = amount
        
        keyboard = [
            [
                InlineKeyboardButton("✅ ثبت شرط", callback_data="bet_confirm"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
            ]
        ]
        
        await query.edit_message_text(
            f"🎲 تایید شرط:\n\n"
            f"حریف: {name}\n"
            f"مقدار: {amount} MPYJ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "bet_confirm":
        target_id = context.user_data.get("bet_target")
        amount = context.user_data.get("bet_amount")
        
        if not target_id or not amount:
            await query.edit_message_text("❌ دوباره شروع کن!")
            return
        
        target = get_user(target_id)
        name = target[2] or target[1] or f"کاربر {target_id}"
        
        # کم کردن از موجودی هر دو طرف
        update_balance(user_id, -amount)
        update_balance(target_id, -amount)
        
        # ثبت شرط
        bet_id = create_bet(
            f"Bet {user_id} vs {target_id}",
            user_id, target_id, amount
        )
        
        await query.edit_message_text(
            f"✅ شرط ثبت شد!\n\n"
            f"حریف: {name}\n"
            f"مقدار: {amount} MPYJ\n"
            f"شماره شرط: #{bet_id}\n\n"
            f"💰 {amount} از هر دو طرف کم شد"
        )
        
        context.user_data.pop("bet_target", None)
        context.user_data.pop("bet_amount", None)
    
    # ==================== ادمین ====================
    elif data == "admin_cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ لغو شد.")
        return
    
    elif data.startswith("admin_add_"):
        target_id = int(data.replace("admin_add_", ""))
        target = get_user(target_id)
        if not target:
            await query.edit_message_text("❌ کاربر پیدا نشد!")
            return
        
        context.user_data["admin_action"] = "add"
        context.user_data["admin_target"] = target_id
        
        name = target[2] or target[1] or f"کاربر {target_id}"
        await query.edit_message_text(
            f"➕ چقدر به {name} اضافه کنم؟\n\n"
            f"یه عدد بفرست (یا /cancel بزن)"
        )
    
    elif data.startswith("admin_remove_"):
        target_id = int(data.replace("admin_remove_", ""))
        target = get_user(target_id)
        if not target:
            await query.edit_message_text("❌ کاربر پیدا نشد!")
            return
        
        context.user_data["admin_action"] = "remove"
        context.user_data["admin_target"] = target_id
        
        name = target[2] or target[1] or f"کاربر {target_id}"
        await query.edit_message_text(
            f"➖ چقدر از {name} کم کنم؟\n\n"
            f"یه عدد بفرست (یا /cancel بزن)"
        )

# ========== message handler ==========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # ===== انتظار مقدار دلخواه =====
    if "waiting_custom_amount" in context.user_data:
        try:
            amount = int(text)
        except:
            await update.message.reply_text("❌ عدد بفرست!")
            return
        
        mode = context.user_data["waiting_custom_amount"]
        balance = get_balance(user_id)
        
        if amount <= 0:
            await update.message.reply_text("❌ عدد باید بزرگتر از صفر باشه!")
            return
        
        if amount > balance:
            await update.message.reply_text(
                f"❌ موجودیت کافی نیست!\n💰 موجودی: {balance}"
            )
            return
        
        if mode == "send":
            context.user_data["send_amount"] = amount
            target_id = context.user_data.get("send_target")
            target = get_user(target_id)
            name = target[2] or target[1] or f"کاربر {target_id}"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ تایید", callback_data="send_confirm"),
                    InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
                ]
            ]
            await update.message.reply_text(
                f"📤 تایید نهایی:\n\nبه: {name}\nمقدار: {amount} MPYJ",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif mode == "bet":
            context.user_data["bet_amount"] = amount
            target_id = context.user_data.get("bet_target")
            target = get_user(target_id)
            name = target[2] or target[1] or f"کاربر {target_id}"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ ثبت شرط", callback_data="bet_confirm"),
                    InlineKeyboardButton("❌ لغو", callback_data="cancel_all"),
                ]
            ]
            await update.message.reply_text(
                f"🎲 تایید شرط:\n\nحریف: {name}\nمقدار: {amount} MPYJ",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        context.user_data.pop("waiting_custom_amount", None)
        return
    
    # ===== انتظار مقدار ادمین =====
    if user_id == OWNER_TELEGRAM_ID and "admin_action" in context.user_data:
        try:
            amount = int(text)
        except:
            await update.message.reply_text("❌ عدد بفرست!")
            return
        
        action = context.user_data["admin_action"]
        target_id = context.user_data["admin_target"]
        target = get_user(target_id)
        target_name = target[2] or target[1] or f"کاربر {target_id}"
        
        if action == "add":
            update_balance(target_id, amount)
            await update.message.reply_text(f"✅ {amount} MPYJ به {target_name} اضافه شد!")
        elif action == "remove":
            update_balance(target_id, -amount)
            await update.message.reply_text(f"✅ {amount} MPYJ از {target_name} کم شد!")
        
        context.user_data.pop("admin_action", None)
        context.user_data.pop("admin_target", None)
        
        await update.message.reply_text("منوی ادمین:", reply_markup=ADMIN_MENU)
        return
    
    # ===== انتظار پیام همگانی =====
    if user_id == OWNER_TELEGRAM_ID and context.user_data.get("broadcast_mode"):
        context.user_data.pop("broadcast_mode", None)
        users = get_all_users()
        success = 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u[0], text=f"📢 {text}")
                success += 1
            except:
                pass
        await update.message.reply_text(
            f"✅ پیام به {success} نفر فرستاده شد!",
            reply_markup=ADMIN_MENU
        )
        return
    
    # ===== سوییچ منو =====
    if user_id == OWNER_TELEGRAM_ID and text == "👤 منوی کاربری":
        await update.message.reply_text(
            "👤 منوی کاربری:\n(برای برگشت به پنل ادمین، /admin رو بزن)",
            reply_markup=MAIN_MENU
        )
        return
    
    # ===== منوی ادمین =====
    if user_id == OWNER_TELEGRAM_ID:
        if text == "👥 لیست کاربران":
            await show_all_users(update, context)
            return
        elif text == "➕ افزایش موجودی":
            await start_admin_add(update, context)
            return
        elif text == "➖ کاهش موجودی":
            await start_admin_remove(update, context)
            return
        elif text == "📊 آمار کلی":
            await show_stats(update, context)
            return
        elif text == "📢 پیام همگانی":
            await start_broadcast(update, context)
            return
    
    # ===== منوی کاربری =====
    if text == "💰 موجودی":
        await show_balance(update, context)
    
    elif text == "📤 ارسال":
        users = get_all_users_except(user_id)
        if not users:
            await update.message.reply_text("❌ هنوز کاربر دیگه‌ای نیست!")
            return
        
        keyboard = []
        for u in users[:15]:
            name = u[2] or u[1] or f"کاربر {u[0]}"
            keyboard.append([InlineKeyboardButton(
                f"{name}",
                callback_data=f"send_to_{u[0]}"
            )])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
        
        await update.message.reply_text(
            "📤 به کی می‌خوای سکه بفرستی؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif text == "🎲 شرط‌بندی":
        users = get_all_users_except(user_id)
        if not users:
            await update.message.reply_text("❌ هنوز کاربر دیگه‌ای نیست!")
            return
        
        keyboard = []
        for u in users[:15]:
            name = u[2] or u[1] or f"کاربر {u[0]}"
            keyboard.append([InlineKeyboardButton(
                f"{name}",
                callback_data=f"bet_with_{u[0]}"
            )])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
        
        await update.message.reply_text(
            "🎲 با کی می‌خوای شرط ببندی؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif text == "🏆 رتبه‌ها":
        await show_leaderboard(update, context)
    elif text == "👤 پروفایل":
        await show_profile(update, context)
    elif text == "❓ راهنما":
        await update.message.reply_text(
            "📖 راهنما:\n💰 موجودی\n📤 ارسال\n🎲 شرط‌بندی\n🏆 رتبه‌ها\n👤 پروفایل"
        )
    elif text == "🔙 برگشت به منوی اصلی":
        await update.message.reply_text("منوی اصلی:", reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text("❓ از منو انتخاب کن یا /help بزن.")

# ========== لیست کاربران (ادمین) ==========
async def show_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("هنوز کسی عضو نشده!")
        return
    
    text = f"👥 لیست کاربران ({len(users)} نفر)\n\n"
    for u in users[:30]:
        name = u[2] or u[1] or f"کاربر {u[0]}"
        text += f"• {name} → {u[3] or 0} MPYJ\n"
        text += f"  آیدی: {u[0]}\n"
    
    if len(users) > 30:
        text += f"\n... و {len(users) - 30} نفر دیگه"
    
    await update.message.reply_text(text)

# ========== شروع افزایش موجودی ==========
async def start_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:10]:
        name = u[2] or u[1] or f"کاربر {u[0]}"
        keyboard.append([InlineKeyboardButton(
            f"{name} ({u[3] or 0} MPYJ)",
            callback_data=f"admin_add_{u[0]}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="admin_cancel")])
    
    await update.message.reply_text(
        "➕ به کی می‌خوای سکه بدی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== شروع کاهش موجودی ==========
async def start_admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:10]:
        name = u[2] or u[1] or f"کاربر {u[0]}"
        keyboard.append([InlineKeyboardButton(
            f"{name} ({u[3] or 0} MPYJ)",
            callback_data=f"admin_remove_{u[0]}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="admin_cancel")])
    
    await update.message.reply_text(
        "➖ از کی می‌خوای سکه کم کنی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== آمار کلی (ادمین) ==========
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    total_users = len(users)
    total_coins = sum(u[3] or 0 for u in users)
    richest = max(users, key=lambda x: x[3] or 0) if users else None
    
    text = f"📊 آمار کلی Mpyj\n\n"
    text += f"👥 تعداد کاربران: {total_users}\n"
    text += f"💰 مجموع سکه‌ها: {total_coins} MPYJ\n"
    if richest:
        name = richest[2] or richest[1] or f"کاربر {richest[0]}"
        text += f"👑 ثروتمندترین: {name} ({richest[3]} MPYJ)"
    
    await update.message.reply_text(text)

# ========== شروع پیام همگانی ==========
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_mode"] = True
    await update.message.reply_text(
        "📢 متن پیام همگانی رو بنویس:\n(یا /cancel بزن)"
    )

# ========== نمایش موجودی ==========
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ اول /start رو بزن!")
        return
    balance = get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 موجودی تو: {balance} MPYJ")

# ========== پروفایل ==========
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ اول /start رو بزن!")
        return
    
    balance = get_balance(update.effective_user.id)
    await update.message.reply_text(
        f"👤 پروفایل تو\n\n"
        f"🆔 آیدی: {user[0]}\n"
        f"📛 نام: {user[2] or 'نداری'}\n"
        f"💰 موجودی: {balance} MPYJ"
    )

# ========== رتبه‌بندی ==========
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("هنوز کسی عضو نشده!")
        return
    
    sorted_users = sorted(users, key=lambda x: x[3] or 0, reverse=True)
    
    text = "🏆 جدول رتبه‌بندی\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(sorted_users[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = u[2] or u[1] or f"کاربر {u[0]}"
        text += f"{medal} {name} → {u[3] or 0} MPYJ\n"
    
    await update.message.reply_text(text)

# ========== /send ==========
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ فرمت: /send @username 50")
        return
    
    target_username = context.args[0].replace("@", "")
    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❌ مقدار باید عدد باشه!")
        return
    
    target = get_user_by_username(target_username)
    if not target:
        await update.message.reply_text(f"❌ کاربر @{target_username} پیدا نشد!")
        return
    
    success, msg = transfer(user.id, target[0], amount, "send")
    if success:
        await update.message.reply_text(f"✅ {amount} MPYJ به @{target_username} فرستاده شد!")
    else:
        await update.message.reply_text(f"❌ {msg}")

# ========== /reward (ادمین) ==========
async def reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_TELEGRAM_ID:
        await update.message.reply_text("❌ فقط مالک!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ فرمت: /reward @username 50 دلیل")
        return
    
    target_username = context.args[0].replace("@", "")
    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❌ مقدار باید عدد باشه!")
        return
    
    target = get_user_by_username(target_username)
    if not target:
        await update.message.reply_text(f"❌ کاربر @{target_username} پیدا نشد!")
        return
    
    update_balance(target[0], amount)
    await update.message.reply_text(f"🎁 {amount} MPYJ به @{target_username} داده شد!")

# ========== /cancel ==========
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    menu = ADMIN_MENU if update.effective_user.id == OWNER_TELEGRAM_ID else MAIN_MENU
    await update.message.reply_text("لغو شد.", reply_markup=menu)

# ========== main ==========
def main():
    init_db()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("reward", reward_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🤖 ربات Mpyj روشن شد!")
    print(f"👑 Owner ID: {OWNER_TELEGRAM_ID}")
    app.run_polling()

if __name__ == "__main__":
    main()