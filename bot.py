import os
import json
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CLICK BAZAR BOT - CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8692201266:AAFJo8CK6_oRn3bE0we10wtoaMDTWjhGDlI")

# अपने Telegram numeric ID से बदलें
ADMIN_ID = 1881432851

# USER MINI APP
MINI_APP_URL = "https://keshvbari-beep.github.io/Click-bazar-/"

# Local data file
DATA_FILE = "deals.json"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

def load_deals():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def save_deals(deals):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            deals,
            file,
            ensure_ascii=False,
            indent=2
        )


def get_next_id():
    deals = load_deals()

    if not deals:
        return 1

    return max(int(deal["id"]) for deal in deals) + 1


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id):
    return user_id == ADMIN_ID


# =========================================================
# /START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🛍️ Open Click Bazar",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                "🔥 New Deals",
                callback_data="new_deals"
            )
        ]
    ]

    text = (
        "🛍️ <b>Welcome to Click Bazar</b>\n\n"
        "🔥 New & Best Deals देखने के लिए "
        "नीचे दिए गए button पर क्लिक करें।\n\n"
        "✨ Best Deals • Smart Shopping • New Offers\n\n"
        "👇 अभी Click Bazar खोलें:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# /NEW
# =========================================================

async def new_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    deals = load_deals()

    if not deals:

        await update.message.reply_text(
            "🔥 <b>NEW DEALS</b>\n\n"
            "अभी कोई नई deal available नहीं है।\n\n"
            "थोड़ी देर बाद फिर से /new check करें।",
            parse_mode="HTML"
        )

        return

    text = "🔥 <b>NEW DEALS</b>\n\n"

    buttons = []

    for deal in deals:

        title = deal["title"]
        price = deal["price"]
        link = deal["link"]

        text += (
            f"🛍️ <b>{title}</b>\n"
            f"💰 Price: <b>₹{price}</b>\n\n"
        )

        buttons.append([
            InlineKeyboardButton(
                f"🛒 View Deal • ₹{price}",
                url=link
            )
        ])

    text += (
        "━━━━━━━━━━━━━━━━\n"
        "🛍️ <b>Click Bazar</b>\n"
        "🔥 नई deals देखने के लिए /new"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================================================
# NEW DEAL BUTTON
# =========================================================

async def new_deals_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    deals = load_deals()

    if not deals:

        await query.message.reply_text(
            "🔥 <b>NEW DEALS</b>\n\n"
            "अभी कोई नई deal available नहीं है।",
            parse_mode="HTML"
        )

        return

    text = "🔥 <b>NEW DEALS</b>\n\n"

    buttons = []

    for deal in deals:

        title = deal["title"]
        price = deal["price"]
        link = deal["link"]

        text += (
            f"🛍️ <b>{title}</b>\n"
            f"💰 Price: <b>₹{price}</b>\n\n"
        )

        buttons.append([
            InlineKeyboardButton(
                f"🛒 View Deal • ₹{price}",
                url=link
            )
        ])

    await query.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================================================
# ADMIN PANEL COMMAND
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ <b>Access Denied</b>",
            parse_mode="HTML"
        )

        return

    text = (
        "🔐 <b>CLICK BAZAR ADMIN</b>\n\n"

        "➕ <b>/add</b>\n"
        "नई deal जोड़ें\n\n"

        "📋 <b>/list</b>\n"
        "सभी deals देखें\n\n"

        "🗑️ <b>/delete ID</b>\n"
        "Deal हटाएँ\n\n"

        "❌ <b>/cancel</b>\n"
        "Current action cancel करें"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# ADD DEAL
# =========================================================

ADD_TITLE, ADD_PRICE, ADD_LINK = range(3)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Access Denied."
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "➕ <b>ADD NEW DEAL</b>\n\n"
        "Step 1/3\n\n"
        "📝 Product का नाम भेजें:",
        parse_mode="HTML"
    )

    return ADD_TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["title"] = update.message.text.strip()

    await update.message.reply_text(
        "💰 <b>Step 2/3</b>\n\n"
        "Product की price भेजें।\n\n"
        "Example: <code>499</code>",
        parse_mode="HTML"
    )

    return ADD_PRICE


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = update.message.text.strip()

    price = (
        price
        .replace("₹", "")
        .replace(",", "")
        .strip()
    )

    try:
        float(price)
    except ValueError:

        await update.message.reply_text(
            "❌ सही price भेजें।\n\n"
            "Example: <code>499</code>",
            parse_mode="HTML"
        )

        return ADD_PRICE

    context.user_data["price"] = price

    await update.message.reply_text(
        "🔗 <b>Step 3/3</b>\n\n"
        "अब product/deal link भेजें:",
        parse_mode="HTML"
    )

    return ADD_LINK


async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    link = update.message.text.strip()

    if not (
        link.startswith("https://")
        or link.startswith("http://")
    ):

        await update.message.reply_text(
            "❌ Valid link भेजें।\n\n"
            "Link <code>https://</code> से शुरू होना चाहिए।",
            parse_mode="HTML"
        )

        return ADD_LINK

    title = context.user_data["title"]
    price = context.user_data["price"]

    deals = load_deals()

    new_deal = {
        "id": get_next_id(),
        "title": title,
        "price": price,
        "link": link
    }

    deals.append(new_deal)

    save_deals(deals)

    await update.message.reply_text(
        "✅ <b>DEAL ADDED!</b>\n\n"
        f"🆔 ID: <code>{new_deal['id']}</code>\n"
        f"🛍️ {title}\n"
        f"💰 ₹{price}\n\n"
        "अब यह deal /new में दिखाई देगी।",
        parse_mode="HTML"
    )

    context.user_data.clear()

    return ConversationHandler.END


# =========================================================
# CANCEL
# =========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Action cancelled."
    )

    return ConversationHandler.END


# =========================================================
# ADMIN LIST
# =========================================================

async def list_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Access Denied."
        )

        return

    deals = load_deals()

    if not deals:

        await update.message.reply_text(
            "📋 अभी कोई deal नहीं है।"
        )

        return

    text = "📋 <b>ALL DEALS</b>\n\n"

    for deal in deals:

        text += (
            f"🆔 <code>{deal['id']}</code>\n"
            f"🛍️ {deal['title']}\n"
            f"💰 ₹{deal['price']}\n"
            f"🔗 {deal['link']}\n"
            "━━━━━━━━━━━━━━\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# DELETE DEAL
# =========================================================

async def delete_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Access Denied."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "❌ Deal ID दें।\n\n"
            "Example:\n"
            "<code>/delete 3</code>",
            parse_mode="HTML"
        )

        return

    try:
        deal_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid Deal ID."
        )

        return

    deals = load_deals()

    updated = [
        deal
        for deal in deals
        if int(deal["id"]) != deal_id
    ]

    if len(updated) == len(deals):

        await update.message.reply_text(
            f"❌ Deal ID {deal_id} नहीं मिली।"
        )

        return

    save_deals(updated)

    await update.message.reply_text(
        f"✅ Deal ID {deal_id} delete हो गई।"
    )


# =========================================================
# RANDOM USER MESSAGE
# =========================================================

async def random_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Admin को random message पर block message नहीं चाहिए
    if is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "❌ <b>Invalid Message</b>\n\n"
        "कृपया available commands का इस्तेमाल करें।\n\n"
        "🔥 New Deals → /new\n"
        "🛍️ Click Bazar → /start",
        parse_mode="HTML"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if BOT_TOKEN == "PASTE_BOT_TOKEN_HERE":

        print("❌ BOT_TOKEN सेट करें।")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # -----------------------------
    # ADD DEAL CONVERSATION
    # -----------------------------

    add_conversation = ConversationHandler(

        entry_points=[
            CommandHandler("add", add_start)
        ],

        states={

            ADD_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_title
                )
            ],

            ADD_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_price
                )
            ],

            ADD_LINK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    add_link
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ]
    )

    # -----------------------------
    # COMMANDS
    # -----------------------------

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("new", new_deals)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    app.add_handler(
        CommandHandler("list", list_deals)
    )

    app.add_handler(
        CommandHandler("delete", delete_deal)
    )

    # -----------------------------
    # ADD DEAL
    # -----------------------------

    app.add_handler(add_conversation)

    # -----------------------------
    # BUTTONS
    # -----------------------------

    app.add_handler(
        CallbackQueryHandler(
            new_deals_button,
            pattern="^new_deals$"
        )
    )

    # -----------------------------
    # RANDOM MESSAGES
    # -----------------------------

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            random_message
        )
    )

    print("-----------------------------------")
    print("🛍️ CLICK BAZAR BOT")
    print("✅ Bot is running...")
    print("-----------------------------------")

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================

if __name__ == "__main__":
    main()
