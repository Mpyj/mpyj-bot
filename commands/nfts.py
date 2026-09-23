from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import (
    get_user, get_user_nfts, has_user_nft, give_user_nft,
    get_all_nft_types, get_nft_type
)
from blockchain import get_balance
from commands.helpers import format_number


async def show_nfts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش NFT های موجود"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ اول /start بزن!")
        return
    
    balance = get_balance(user["wallet_address"])
    user_nfts = get_user_nfts(user_id)
    owned = [n["nft_type"] for n in user_nfts]
    
    nft_types = get_all_nft_types()
    
    if not nft_types:
        await update.message.reply_text("⚠️ هنوز NFT ساخته نشده!")
        return
    
    text = f"🎨 NFT های Mpyj\n\n━━━━━━━━━━━━━━━\n"
    text += f"💰 موجودی: {format_number(balance)} MPYJ\n"
    text += f"🏆 NFT های تو: {len(user_nfts)}\n"
    text += f"━━━━━━━━━━━━━━━\n\n"
    
    keyboard = []
    for nft in nft_types:
        if nft["type_id"] in owned:
            text += f"✅ {nft['emoji']} {nft['name']}\n"
            text += f"     💰 {format_number(nft['required'])} MPYJ\n"
        else:
            text += f"🔒 {nft['emoji']} {nft['name']}\n"
            text += f"     💰 {format_number(nft['required'])} MPYJ\n"
        
        if nft.get("reward") and nft["reward"] != "بدون جایزه ویژه":
            text += f"     🎁 {nft['reward']}\n"
        text += "\n"
        
        if nft["type_id"] not in owned and balance >= nft["required"]:
            keyboard.append([InlineKeyboardButton(
                f"🎁 دریافت {nft['name']}",
                callback_data=f"nft_claim_{nft['type_id']}"
            )])
    
    keyboard.append([InlineKeyboardButton("❌ بستن", callback_data="cancel_all")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def claim_nft_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت NFT + ارسال عکس"""
    query = update.callback_query
    await query.answer()
    
    type_id = query.data.replace("nft_claim_", "")
    user_id = query.from_user.id
    
    nft = get_nft_type(type_id)
    if not nft:
        await query.edit_message_text("⚠️ NFT نامعتبر!")
        return
    
    user = get_user(user_id)
    if not user:
        await query.edit_message_text("⚠️ کاربر پیدا نشد!")
        return
    
    # چک کن قبلاً نگرفته
    if has_user_nft(user_id, type_id):
        await query.edit_message_text("⚠️ قبلاً این NFT رو گرفتی!")
        return
    
    # چک موجودی
    balance = get_balance(user["wallet_address"])
    if balance < nft["required"]:
        await query.edit_message_text(
            f"❌ موجودیت کافی نیست!\n\n"
            f"💰 {format_number(balance)} < {format_number(nft['required'])} MPYJ"
        )
        return
    
    # ثبت NFT
    give_user_nft(user_id, type_id)
    
    # اگه عکس داشت، بفرست
    if nft.get("photo_file_id"):
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=nft["photo_file_id"],
                caption=(
                    f"🎉 **NFT گرفتی!**\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{nft['emoji']} {nft['name']}\n"
                    f"━━━━━━━━━━━━━━━\n\n"
                    f"این NFT تو پروفایلت ذخیره شد! 🎊"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ send_photo error: {e}")
            await query.edit_message_text(
                f"✅ {nft['name']} گرفتی!\n"
                f"(عکس به‌زودی فرستاده میشه)"
            )
    else:
        await query.edit_message_text(
            f"✅ {nft['name']} گرفتی!\n"
            f"(عکس هنوز آپلود نشده)"
        )
    
    # اگه جایزه ویژه داشت، به ادمین اطلاع بده
    from config import OWNER_TELEGRAM_ID
    
    if nft.get("reward") and nft["reward"] != "بدون جایزه ویژه":
        try:
            await context.bot.send_message(
                chat_id=OWNER_TELEGRAM_ID,
                text=(
                    f"🎁 درخواست جایزه ویژه!\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👤 کاربر: {user['first_name'] or user['username']}\n"
                    f"🆔 آیدی: {user_id}\n"
                    f"🏆 NFT: {nft['name']}\n"
                    f"🎁 جایزه: {nft['reward']}\n"
                    f"━━━━━━━━━━━━━━━\n\n"
                    f"از پنل ادمین پیگیری کن!"
                )
            )
        except:
            pass
        
        # پیام به کاربر
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎁 **جایزه ویژه!**\n\n"
                    f"به‌خاطر گرفتن {nft['name']}\n"
                    f"مستحق {nft['reward']} شدی!\n\n"
                    f"⏳ به ادمین اطلاع دادیم\n"
                    f"به‌زودی باهات تماس می‌گیره."
                ),
                parse_mode="Markdown"
            )
        except:
            pass


async def show_my_nfts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش NFT های کاربر"""
    user_id = update.effective_user.id
    user_nfts = get_user_nfts(user_id)
    
    if not user_nfts:
        await update.message.reply_text(
            "🎨 NFT ها\n\n"
            "━━━━━━━━━━━━━━━\n"
            "هنوز NFT نداری!\n\n"
            "💡 با جمع کردن MPYJ بیشتر،\n"
            "NFT های ویژه بگیر"
        )
        return
    
    text = f"🎨 NFT های تو ({len(user_nfts)})\n\n━━━━━━━━━━━━━━━\n"
    
    for unft in user_nfts:
        nft = get_nft_type(unft["nft_type"])
        if nft:
            claimed = "✅" if unft.get("claimed") else "⏳"
            text += f"{nft['emoji']} {nft['name']} {claimed}\n"
    
    text += "\n━━━━━━━━━━━━━━━"
    text += "\n\n💡 ✅ = تحویل داده شده"
    text += "\n💡 ⏳ = در انتظار تحویل"
    
    await update.message.reply_text(text)