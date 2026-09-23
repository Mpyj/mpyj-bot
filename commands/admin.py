from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_TELEGRAM_ID
from database import (
    get_all_users, get_user, get_all_pending_rewards,
    get_pending_reward, update_pending_reward_status, add_history,
    get_pending_bets, get_bet, update_bet_status,
    create_nft_type, get_all_nft_types, get_nft_type,
    update_nft_photo, get_user_nfts, claim_user_nft
)
from blockchain import (
    get_balance, get_owner_eth_balance, get_owner_token_balance,
    reward_winner, send_tokens_from_owner
)
from commands.helpers import format_number, ADMIN_MENU


def is_owner(user_id):
    return user_id == OWNER_TELEGRAM_ID


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ فقط مالک!")
        return
    
    await update.message.reply_text(
        "👑 پنل ادمین Mpyj\n\n"
        "━━━━━━━━━━━━━━━\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=ADMIN_MENU
    )


async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    text = f"👥 لیست کاربران ({len(users)} نفر)\n\n━━━━━━━━━━━━━━━\n"
    for u in users[:30]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        bal = get_balance(u["wallet_address"])
        text += f"👤 {name}\n     💰 {format_number(bal)} MPYJ\n"
        text += f"     🆔 {u['telegram_id']}\n\n"
    
    await update.message.reply_text(text)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    total_users = len(users)
    
    await update.message.reply_text("⏳ در حال محاسبه...")
    
    total_coins = 0
    richest = None
    max_bal = 0
    for u in users:
        bal = get_balance(u["wallet_address"])
        total_coins += bal
        if bal > max_bal:
            max_bal = bal
            richest = u
    
    eth_bal = get_owner_eth_balance()
    token_bal = get_owner_token_balance()
    pending = get_all_pending_rewards()
    pending_bets = get_pending_bets()
    
    text = f"📊 آمار کلی Mpyj\n\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"👥 کاربران: {total_users}\n"
    text += f"💰 مجموع سکه: {format_number(total_coins)} MPYJ\n"
    if richest:
        name = richest["first_name"] or richest["username"] or "ناشناس"
        text += f"👑 ثروتمندترین: {name} ({format_number(max_bal)})\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"⛽ ETH Owner: {eth_bal:.4f}\n"
    text += f"🪙 MPYJ Owner: {format_number(token_bal)}\n"
    text += f"🎁 جوایز در انتظار: {len(pending)}\n"
    text += f"🎲 شرط‌های در انتظار: {len(pending_bets)}\n"
    text += f"━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(text)


# ==================== جوایز در انتظار ====================
async def show_pending_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جوایز در انتظار + کانفیگ و برنامه‌نویسی"""
    if not is_owner(update.effective_user.id):
        return
    
    rewards = get_all_pending_rewards()
    
    # پیدا کردن کاربرایی که NFT ویژه گرفتن
    special_users = []
    for u in get_all_users():
        nfts = get_user_nfts(u["telegram_id"])
        for nft in nfts:
            if nft["nft_type"] in ["legend", "champion"] and not nft.get("claimed"):
                special_users.append({
                    "user": u,
                    "nft": nft,
                })
    
    text = "🎯 جوایز در انتظار\n\n"
    text += "━━━━━━━━━━━━━━━\n"
    
    if not rewards and not special_users:
        text += "هیچ جایزه‌ای در انتظار نیست!"
        await update.message.reply_text(text)
        return
    
    keyboard = []
    
    # ===== جوایز MPYJ =====
    if rewards:
        text += f"\n💰 جوایز MPYJ ({len(rewards)})\n\n"
        for r in rewards[:5]:
            user = get_user(r["user_id"])
            name = user["first_name"] or user["username"] or f"کاربر {r['user_id']}"
            
            text += f"🆔 #{r['id']} | 👤 {name}\n"
            text += f"💰 {r['amount']} MPYJ | 🔖 {r['reason']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"✅ تایید #{r['id']}", callback_data=f"approve_reward_{r['id']}"),
                InlineKeyboardButton(f"❌ رد #{r['id']}", callback_data=f"reject_reward_{r['id']}"),
            ])
    
    # ===== جوایز کانفیگ VPN =====
    config_users = [s for s in special_users if s["nft"]["nft_type"] == "legend"]
    if config_users:
        text += f"\n🎁 جوایز کانفیگ VPN ({len(config_users)})\n\n"
        for s in config_users:
            u = s["user"]
            nft = s["nft"]
            name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
            
            text += f"👤 {name}\n"
            text += f"🏆 {nft['nft_name']}\n"
            text += f"🎁 جایزه: کانفیگ رایگان VPN\n"
            text += f"🆔 آیدی: {u['telegram_id']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🎁 تحویل کانفیگ به {name[:12]}",
                    callback_data=f"claim_special_config_{nft['id']}_{u['telegram_id']}"
                )
            ])
    
    # ===== جوایز برنامه‌نویسی =====
    prog_users = [s for s in special_users if s["nft"]["nft_type"] == "champion"]
    if prog_users:
        text += f"\n💻 جوایز برنامه‌نویسی ({len(prog_users)})\n\n"
        for s in prog_users:
            u = s["user"]
            nft = s["nft"]
            name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
            
            text += f"👤 {name}\n"
            text += f"🏆 {nft['nft_name']}\n"
            text += f"🎁 جایزه: سفارش برنامه‌نویسی اختصاصی\n"
            text += f"🆔 آیدی: {u['telegram_id']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"💻 تحویل برنامه‌نویسی به {name[:12]}",
                    callback_data=f"claim_special_programming_{nft['id']}_{u['telegram_id']}"
                )
            ])
    
    text += "━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== مدیریت NFT ====================
async def manage_nfts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت NFT ها (ادمین)"""
    if not is_owner(update.effective_user.id):
        return
    
    nfts = get_all_nft_types()
    
    if not nfts:
        keyboard = [
            [InlineKeyboardButton("➕ ساخت NFT پیش‌فرض", callback_data="nft_create_defaults")],
        ]
        await update.message.reply_text(
            "🎨 مدیریت NFT ها\n\n"
            "━━━━━━━━━━━━━━━\n"
            "هنوز NFT نساختی!\n\n"
            "💡 با دکمه زیر، ۶ تا NFT پیش‌فرض بساز:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    text = "🎨 مدیریت NFT ها\n\n━━━━━━━━━━━━━━━\n"
    
    for nft in nfts:
        has_photo = "✅" if nft.get("photo_file_id") else "❌"
        text += f"{nft['emoji']} {nft['name']}\n"
        text += f"     💰 {format_number(nft['required'])} MPYJ\n"
        text += f"     🖼️ عکس: {has_photo}\n\n"
    
    text += "━━━━━━━━━━━━━━━\n"
    text += "💡 برای آپلود عکس، از دکمه\n"
    text += "🖼️ آپلود عکس NFT استفاده کن"
    
    await update.message.reply_text(text)


async def create_default_nfts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ساخت ۶ NFT پیش‌فرض"""
    query = update.callback_query
    await query.answer()
    
    if not is_owner(query.from_user.id):
        return
    
    defaults = [
        ("bronze", "🥉 مدال برنز", "🥉", 100, "بدون جایزه ویژه"),
        ("silver", "🥈 مدال نقره", "🥈", 500, "بدون جایزه ویژه"),
        ("gold", "🥇 مدال طلا", "🥇", 2000, "بدون جایزه ویژه"),
        ("diamond", "💎 جواهر", "💎", 5000, "بدون جایزه ویژه"),
        ("legend", "👑 تاج افسانه", "👑", 10000, "🎁 کانفیگ رایگان VPN"),
        ("champion", "🏆 جام قهرمانی", "🏆", 50000, "🎁 سفارش برنامه‌نویسی"),
    ]
    
    created = 0
    for type_id, name, emoji, required, reward in defaults:
        nft_id, error = create_nft_type(type_id, name, emoji, required, reward, None)
        if not error:
            created += 1
    
    await query.edit_message_text(
        f"✅ {created} NFT پیش‌فرض ساخته شد!\n\n"
        f"حالا از 🖼️ آپلود عکس NFT استفاده کن."
    )


async def start_upload_nft_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع آپلود عکس NFT"""
    if not is_owner(update.effective_user.id):
        return
    
    nfts = get_all_nft_types()
    
    if not nfts:
        await update.message.reply_text(
            "⚠️ هنوز NFT نساختی!\n\n"
            "اول برو تو 🎨 مدیریت NFT → ساخت NFT پیش‌فرض"
        )
        return
    
    keyboard = []
    for nft in nfts:
        has_photo = "✅" if nft.get("photo_file_id") else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{has_photo} {nft['emoji']} {nft['name']}",
            callback_data=f"upload_nft_{nft['type_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "🖼️ آپلود عکس NFT\n\n"
        "━━━━━━━━━━━━━━━\n"
        "کدوم NFT رو می‌خوای عکسش رو آپلود کنی؟\n\n"
        "✅ = عکس داره\n"
        "❌ = عکس نداره",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_nft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /setnft <type_id>"""
    if not is_owner(update.effective_user.id):
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ فرمت: `/setnft <type_id>`\n\n"
            "مثال: `/setnft bronze`",
            parse_mode="Markdown"
        )
        return
    
    type_id = context.args[0]
    nft = get_nft_type(type_id)
    
    if not nft:
        await update.message.reply_text(f"⚠️ NFT با شناسه {type_id} پیدا نشد!")
        return
    
    context.user_data["setnft_type"] = type_id
    
    await update.message.reply_text(
        f"🖼️ آپلود عکس برای {nft['name']}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"حالا عکس رو بفرست (به صورت Photo)"
    )


async def handle_nft_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل عکس NFT"""
    if not is_owner(update.effective_user.id):
        return
    
    type_id = context.user_data.get("setnft_type")
    if not type_id:
        return
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    update_nft_photo(type_id, file_id)
    
    nft = get_nft_type(type_id)
    context.user_data.pop("setnft_type", None)
    
    await update.message.reply_text(
        f"✅ عکس برای {nft['name']} ذخیره شد!\n\n"
        f"حالا وقتی کاربر واجد شرایط بشه،\n"
        f"این عکس بهش فرستاده میشه."
    )


# ==================== شرط‌های در انتظار ====================
async def show_pending_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    bets = get_pending_bets()
    
    if not bets:
        await update.message.reply_text(
            "🎲 شرط‌های در انتظار\n\n"
            "━━━━━━━━━━━━━━━\n"
            "هیچ شرطی در انتظار نیست!"
        )
        return
    
    text = f"🎲 شرط‌های در انتظار ({len(bets)} مورد)\n\n━━━━━━━━━━━━━━━\n"
    
    keyboard = []
    for b in bets[:10]:
        p1 = get_user(b["player1_id"])
        p2 = get_user(b["player2_id"])
        n1 = p1["first_name"] or p1["username"] or "کاربر"
        n2 = p2["first_name"] or p2["username"] or "کاربر"
        
        text += f"🆔 #{b['id']}\n"
        text += f"📝 {b['title']}\n"
        text += f"👤 {n1} vs {n2}\n"
        text += f"💰 {b['amount']} MPYJ\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"🏆 {n1}", callback_data=f"settle_{b['id']}_1"),
            InlineKeyboardButton(f"🏆 {n2}", callback_data=f"settle_{b['id']}_2"),
        ])
    
    text += "━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== جایزه دادن ====================
async def start_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"🎁 {name}",
            callback_data=f"reward_to_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "🎁 به کی جایزه بدم؟\n\n"
        "━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_reward_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_id = int(query.data.replace("reward_to_", ""))
    context.user_data["reward_target"] = target_id
    
    target = get_user(target_id)
    name = target["first_name"] or target["username"] or f"کاربر {target_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 ۵۰", callback_data="reward_amt_50"),
            InlineKeyboardButton("🎁 ۱۰۰", callback_data="reward_amt_100"),
            InlineKeyboardButton("🎁 ۵۰۰", callback_data="reward_amt_500"),
        ],
        [
            InlineKeyboardButton("🏆 ۱۰۰۰", callback_data="reward_amt_1000"),
            InlineKeyboardButton("🏆 ۵۰۰۰", callback_data="reward_amt_5000"),
        ],
        [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="reward_amt_custom")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_all")],
    ]
    
    await query.edit_message_text(
        f"🎁 جایزه به {name}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"چقدر جایزه بدم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== افزایش/کاهش ====================
async def start_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("😴 هنوز کسی عضو نشده!")
        return
    
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"➕ {name}",
            callback_data=f"admin_add_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "➕ به کی سکه بدم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    
    users = get_all_users()
    keyboard = []
    for u in users[:15]:
        name = u["first_name"] or u["username"] or f"کاربر {u['telegram_id']}"
        keyboard.append([InlineKeyboardButton(
            f"➖ {name}",
            callback_data=f"admin_remove_{u['telegram_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel_all")])
    
    await update.message.reply_text(
        "➖ از کی سکه کم کنم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== پیام همگانی ====================
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    context.user_data["broadcast_mode"] = True
    await update.message.reply_text(
        "📢 پیام همگانی\n\n"
        "متن پیام رو بنویس:\n"
        "(یا /cancel بزن)"
    )