import os
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_BOT_TOKEN_HERE")

# IMPORTANT:
# Yahan apne CURRENT working bot.py wala ADMIN_ID hi rakho.
ADMIN_ID = 1881432851

MINI_APP_URL = "https://keshvbari-beep.github.io/Click-bazar-/"
DATA_FILE = "deals.json"

ADD_TITLE, ADD_PRICE, ADD_LINK = range(3)


# =========================
# RENDER HTTP SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Click Bazar Bot is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"HTTP server running on port {port}")
    server.serve_forever()


# =========================
# DEAL STORAGE
# =========================

def load_deals():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_deals(deals):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)


def get_next_id(deals):
    if not deals:
        return 1

    return max(int(d["id"]) for d in deals) + 1


# =========================
# ADMIN CHECK
# =========================

def is_admin(update: Update):
    user = update.effective_user

    if not user:
        return False

    return user.id == ADMIN_ID


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🛍️ Open Click Bazar",
                url=MINI_APP_URL
            )
        ],
        [
            InlineKeyboardButton(
                "🔥 New Deals",
                callback_data="new_deals"
            )
        ]
    ]

    message = (
        "🛍️ *Welcome to Click Bazar*\n\n"
        "🔥 New & Best Deals देखने के लिए नीचे दिए गए button पर क्लिक करें।\n\n"
        "✨ Best Deals • Smart Shopping • New Offers\n\n"
        "👇 अभी Click Bazar खोलें:"
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# NEW DEALS
# =========================

async def new_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    deals = load_deals()

    if not deals:
        text = (
            "🔥 *NEW DEALS*\n\n"
            "अभी कोई नई deal उपलब्ध नहीं है।"
        )

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(
                text,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="Markdown"
            )

        return

    text = "🔥 *NEW DEALS*\n\n"

    keyboard = []

    for deal in deals:
        text += (
            f"🛍️ *{deal['title']}*\n"
            f"💰 Price: ₹{deal['price']}\n\n"
            "━━━━━━━━━━━━━━━━\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🛒 Buy Now — ₹{deal['price']}",
                url=deal["link"]
            )
        ])

    text += (
        "🛍️ *Click Bazar*\n"
        "🔥 नई deals देखने के लिए /new"
    )

    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )


# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied")
        return

    text = (
        "🔐 *CLICK BAZAR ADMIN*\n\n"
        "➕ /add\n"
        "नई deal जोड़ें\n\n"
        "📋 /list\n"
        "सभी deals देखें\n\n"
        "🗑️ /delete ID\n"
        "Deal हटाएँ\n\n"
        "❌ /cancel\n"
        "Current action cancel करें"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================
# ADD DEAL
# =========================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied")
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "➕ *ADD NEW DEAL*\n\n"
        "Step 1/3\n"
        "📝 Product का नाम भेजें:",
        parse_mode="Markdown"
    )

    return ADD_TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return ConversationHandler.END

    context.user_data["title"] = update.message.text.strip()

    await update.message.reply_text(
        "💰 *Step 2/3*\n\n"
        "Product की price भेजें।\n\n"
        "Example: 499",
        parse_mode="Markdown"
    )

    return ADD_PRICE


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return ConversationHandler.END

    price = update.message.text.strip()

    if not price.replace(".", "", 1).isdigit():
        await update.message.reply_text(
            "❌ सही price भेजें।\n\n"
            "Example: 499"
        )
        return ADD_PRICE

    context.user_data["price"] = price

    await update.message.reply_text(
        "🔗 *Step 3/3*\n\n"
        "अब product/deal link भेजें:",
        parse_mode="Markdown"
    )

    return ADD_LINK


async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return ConversationHandler.END

    link = update.message.text.strip()

    if not (
        link.startswith("http://")
        or link.startswith("https://")
    ):
        await update.message.reply_text(
            "❌ कृपया पूरा valid link भेजें।\n\n"
            "Example:\n"
            "https://www.amazon.in/..."
        )
        return ADD_LINK

    deals = load_deals()

    new_deal = {
        "id": get_next_id(deals),
        "title": context.user_data["title"],
        "price": context.user_data["price"],
        "link": link
    }

    deals.append(new_deal)
    save_deals(deals)

    await update.message.reply_text(
        "✅ *DEAL ADDED SUCCESSFULLY!*\n\n"
        f"🆔 ID: {new_deal['id']}\n"
        f"🛍️ {new_deal['title']}\n"
        f"💰 ₹{new_deal['price']}\n\n"
        "🔥 अब यह /new में दिखाई देगी।",
        parse_mode="Markdown"
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied")
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Current action cancelled."
    )

    return ConversationHandler.END


# =========================
# LIST
# =========================

async def list_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied")
        return

    deals = load_deals()

    if not deals:
        await update.message.reply_text(
            "📋 *ALL DEALS*\n\n"
            "अभी कोई deal नहीं है।",
            parse_mode="Markdown"
        )
        return

    text = "📋 *ALL DEALS*\n\n"

    for deal in deals:
        text += (
            f"🆔 *{deal['id']}*\n"
            f"🛍️ {deal['title']}\n"
            f"💰 ₹{deal['price']}\n"
            f"🔗 {deal['link']}\n"
            "━━━━━━━━━━━━━━\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================
# DELETE
# =========================

async def delete_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text("❌ Access Denied")
        return

    if not context.args:
        await update.message.reply_text(
            "Example:\n/delete 1"
        )
        return

    try:
        deal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ सही ID दें।\n\n"
            "Example: /delete 1"
        )
        return

    deals = load_deals()

    new_deals = [
        d for d in deals
        if int(d["id"]) != deal_id
    ]

    if len(new_deals) == len(deals):
        await update.message.reply_text(
            f"❌ Deal ID {deal_id} नहीं मिली।"
        )
        return

    save_deals(new_deals)

    await update.message.reply_text(
        f"✅ Deal ID {deal_id} deleted successfully."
    )


# =========================
# INVALID MESSAGE
# =========================

async def invalid_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if is_admin(update):
        return

    await update.message.reply_text(
        "❌ *Invalid Message*\n\n"
        "कृपया available commands का इस्तेमाल करें।\n\n"
        "🔥 New Deals → /new\n"
        "🛍️ Click Bazar → /start",
        parse_mode="Markdown"
    )


# =========================
# CALLBACK
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "new_deals":
        await new_deals(update, context)


# =========================
# MAIN
# =========================

def main():

    # Render ke liye HTTP server
    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    print("🛍️ CLICK BAZAR BOT")
    print("✅ Bot is running...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_deals))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("list", list_deals))
    app.add_handler(CommandHandler("delete", delete_deal))

    # Add conversation
    conversation = ConversationHandler(
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
        ],
    )

    app.add_handler(conversation)

    app.add_handler(
        CommandHandler("cancel", cancel)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            invalid_message
        )
    )

    # Telegram polling
    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
