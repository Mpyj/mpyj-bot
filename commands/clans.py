from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_user, get_all_users_except, create_clan, get_clan,
    get_clan_by_name, get_user_clan, add_clan_member,
    remove_clan_member, get_clan_members, get_all_clans,
    create_clan_invite, get_clan_invite, update_clan_invite_status,
    get_pending_invite_for_user, delete_clan
)
from blockchain import get_balance
from commands.helpers import format_number


async def show_clans_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی کلن"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start بزن!")
        return
    
    # چک کن کاربر تو کلنی هست
    membership = get_user_clan(user_id)
    
    if membership:
        # کاربر تو کلن هست
        clan = get_clan(membership["clan_id"])
        members = get_clan_members(clan["id"])
        is_owner = clan["owner_id"] == user_id
        
        text = (
            f"🏰 کلن {clan['name']}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👥 اعضا: {len(members)} نفر\n"
            f"👑 صاحب کلن: {'تو' if is_owner else 'یکی دیگه'}\n"
        )
        if clan.get("description"):
            text += f"📝 {clan['description']}\n"
        text += f"━━━━━━━━━━━━━━━"
        
        keyboard = [
            [InlineKeyboardButton("👥 لیست اعضا", callback_data=f"clan_members_{clan['id']}")],
        ]
        if is_owner:
            keyboard.append([InlineKeyboardButton("➕ دعوت عضو", callback_data=f"clan_invite_{clan['id']}")])
            keyboard.append([InlineKeyboardButton("🗑️ حذف کلن", callback_data=f"clan_delete_{clan['id']}")])
        else:
            keyboard.append([InlineKeyboardButton("🚪 خروج از کلن", callback_data=f"clan_leave_{clan['id']}")])
        keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # کاربر تو کلن نیست
        keyboard = [
            [InlineKeyboardButton("➕ ساخت کلن", callback_data="clan_create")],
            [InlineKeyboardButton("🏆 رتبه‌بندی کلن‌ها", callback_data="clan_leaderboard")],
        ]
        
        # چک کن دعوت pending داره
        invite = get_pending_invite_for_user(user_id)
        if invite:
            clan = get_clan(invite["clan_id"])
            keyboard.insert(0, [InlineKeyboardButton(
                f"📩 دعوت به {clan['name']}",
                callback_data=f"clan_view_invite_{invite['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
        
        await update.message.reply_text(
            "🏰 کلن‌ها\n\n"
            "━━━━━━━━━━━━━━━\n"
            "با دوستانت یه کلن بساز و\n"
            "با کلن‌های دیگه رقابت کن!\n"
            "━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def start_create_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ساخت کلن"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["clan_step"] = "waiting_name"
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_all")]]
    
    await query.edit_message_text(
        "🏰 ساخت کلن\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📝 اسم کلن رو بنویس:\n\n"
        "💡 بین ۳ تا ۲۰ کاراکتر\n"
        "✏️ اسم رو بفرست:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def create_clan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    """ساخت کلن با اسم داده شده"""
    user_id = update.effective_user.id
    
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("⚠️ اسم باید بین ۳ تا ۲۰ کاراکتر باشه!")
        return
    
    # چک کن اسم تکراری نباشه
    existing = get_clan_by_name(name)
    if existing:
        await update.message.reply_text("⚠️ این اسم قبلاً استفاده شده!")
        return
    
    # ساخت کلن
    clan_id, error = create_clan(name, user_id)
    
    if error:
        await update.message.reply_text(f"❌ خطا: {error}")
        return
    
    # اضافه کردن خود کاربر
    add_clan_member(clan_id, user_id)
    
    context.user_data.pop("clan_step", None)
    
    await update.message.reply_text(
        f"🎉 کلن ساخته شد!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏰 اسم: {name}\n"
        f"👑 صاحب: تو\n"
        f"👥 اعضا: ۱ نفر\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"حالا می‌تونی اعضا دعوت کنی!"
    )


async def view_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاهده دعوت کلن"""
    query = update.callback_query
    await query.answer()
    
    invite_id = int(query.data.replace("clan_view_invite_", ""))
    invite = get_clan_invite(invite_id)
    
    if not invite or invite["status"] != "pending":
        await query.edit_message_text("⚠️ این دعوت منقضی شده!")
        return
    
    clan = get_clan(invite["clan_id"])
    inviter = get_user(invite["inviter_id"])
    inviter_name = inviter["first_name"] or inviter["username"] or "کاربر"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"clan_accept_{invite_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"clan_reject_{invite_id}"),
        ]
    ]
    
    await query.edit_message_text(
        f"📩 دعوت به کلن\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏰 کلن: {clan['name']}\n"
        f"👤 از طرف: {inviter_name}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"قبول می‌کنی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def accept_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قبول دعوت کلن"""
    query = update.callback_query
    await query.answer()
    
    invite_id = int(query.data.replace("clan_accept_", ""))
    invite = get_clan_invite(invite_id)
    
    if not invite or invite["status"] != "pending":
        await query.edit_message_text("⚠️ این دعوت منقضی شده!")
        return
    
    user_id = query.from_user.id
    
    if invite["invitee_id"] != user_id:
        await query.answer("⛔ این دعوت برای تو نیست!", show_alert=True)
        return
    
    # چک کن کاربر تو کلن دیگه نباشه
    if get_user_clan(user_id):
        await query.edit_message_text("⚠️ تو تو یه کلن دیگه هستی!")
        return
    
    # اضافه کردن به کلن
    add_clan_member(invite["clan_id"], user_id)
    update_clan_invite_status(invite_id, "accepted")
    
    clan = get_clan(invite["clan_id"])
    
    await query.edit_message_text(
        f"✅ به کلن {clan['name']} پیوستی!\n\n"
        f"🏰 خوش اومدی! 🎉"
    )
    
    # اطلاع به صاحب کلن
    try:
        await context.bot.send_message(
            chat_id=clan["owner_id"],
            text=f"✅ یه کاربر جدید به کلن {clan['name']} پیوست!"
        )
    except:
        pass


async def reject_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد دعوت کلن"""
    query = update.callback_query
    await query.answer()
    
    invite_id = int(query.data.replace("clan_reject_", ""))
    invite = get_clan_invite(invite_id)
    
    if not invite:
        await query.edit_message_text("⚠️ دعوت پیدا نشد!")
        return
    
    update_clan_invite_status(invite_id, "rejected")
    await query.edit_message_text("❌ دعوت رد شد.")


async def invite_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دعوت عضو به کلن"""
    query = update.callback_query
    await query.answer()
    
    clan_id = int(query.data.replace("clan_invite_", ""))
    user_id = query.from_user.id
    
    clan = get_clan(clan_id)
    if not clan or clan["owner_id"] != user_id:
        await query.answer("⛔ فقط صاحب کلن!", show_alert=True)
        return
    
    # لیست کاربران بدون کلن
    users = get_all_users_except(user_id)
    members = get_clan_members(clan_id)
    member_ids = [m["user_id"] for m in members]
    
    keyboard = []
    for u in users[:15]:
        if u["telegram_id"] in member_ids:
            continue
        if get_user_clan(u["telegram_id"]):
            continue  # تو کلن دیگه‌ست
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"clan_invite_to_{clan_id}_{u['telegram_id']}"
        )])
    
    if not keyboard:
        await query.edit_message_text("😴 کاربر آزادی برای دعوت نیست!")
        return
    
    keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
    
    await query.edit_message_text(
        "➕ کی رو دعوت کنم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال دعوت به کاربر"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.replace("clan_invite_to_", "").split("_")
    clan_id = int(parts[0])
    invitee_id = int(parts[1])
    inviter_id = query.from_user.id
    
    clan = get_clan(clan_id)
    invitee = get_user(invitee_id)
    invitee_name = invitee["first_name"] or invitee["username"] or "کاربر"
    
    # ساخت دعوت
    invite_id, error = create_clan_invite(clan_id, inviter_id, invitee_id)
    
    if error:
        await query.edit_message_text(f"❌ خطا: {error}")
        return
    
    # ارسال به کاربر
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"clan_accept_{invite_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"clan_reject_{invite_id}"),
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=invitee_id,
            text=(
                f"📩 دعوت به کلن\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🏰 کلن: {clan['name']}\n"
                f"👤 از طرف: {query.from_user.first_name}\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"قبول می‌کنی؟"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.edit_message_text(f"✅ دعوت به {invitee_name} فرستاده شد!")
    except Exception as e:
        await query.edit_message_text(f"❌ خطا: {e}")


async def show_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اعضای کلن"""
    query = update.callback_query
    await query.answer()
    
    clan_id = int(query.data.replace("clan_members_", ""))
    clan = get_clan(clan_id)
    members = get_clan_members(clan_id)
    
    text = f"👥 اعضای کلن {clan['name']}\n\n━━━━━━━━━━━━━━━\n"
    
    for m in members:
        u = get_user(m["user_id"])
        if not u:
            continue
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        bal = get_balance(u["wallet_address"])
        owner_emoji = "👑 " if u["telegram_id"] == clan["owner_id"] else "👤 "
        text += f"{owner_emoji}{name} → {format_number(bal)} MPYJ\n"
    
    text += "━━━━━━━━━━━━━━━"
    
    await query.edit_message_text(text)


async def leave_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خروج از کلن"""
    query = update.callback_query
    await query.answer()
    
    clan_id = int(query.data.replace("clan_leave_", ""))
    user_id = query.from_user.id
    
    clan = get_clan(clan_id)
    if clan["owner_id"] == user_id:
        await query.answer("⚠️ صاحب کلن نمی‌تونه خارج بشه!", show_alert=True)
        return
    
    remove_clan_member(clan_id, user_id)
    await query.edit_message_text("🚪 از کلن خارج شدی!")


async def delete_clan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کلن"""
    query = update.callback_query
    await query.answer()
    
    clan_id = int(query.data.replace("clan_delete_", ""))
    user_id = query.from_user.id
    
    clan = get_clan(clan_id)
    if clan["owner_id"] != user_id:
        await query.answer("⛔ فقط صاحب کلن!", show_alert=True)
        return
    
    delete_clan(clan_id)
    await query.edit_message_text("🗑️ کلن حذف شد!")


async def show_clan_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رتبه‌بندی کلن‌ها"""
    query = update.callback_query
    await query.answer()
    
    clans = get_all_clans()
    
    if not clans:
        await query.edit_message_text("😴 هنوز کلنی ساخته نشده!")
        return
    
    await query.edit_message_text("⏳ در حال محاسبه...")
    
    # محاسبه مجموع موجودی هر کلن
    clan_balances = []
    for clan in clans:
        members = get_clan_members(clan["id"])
        total = 0
        for m in members:
            u = get_user(m["user_id"])
            if u:
                total += get_balance(u["wallet_address"])
        clan_balances.append((clan["name"], len(members), total))
    
    clan_balances.sort(key=lambda x: x[2], reverse=True)
    
    text = "🏆 رتبه‌بندی کلن‌ها\n\n━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, count, total) in enumerate(clan_balances[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}\n"
        text += f"     👥 {count} عضو | 💰 {format_number(total)}\n\n"
    
    text += "━━━━━━━━━━━━━━━"
    await query.edit_message_text(text)