import os
import logging
import re
from datetime import datetime
from functools import wraps
from typing import Optional, Tuple

import validators
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No bot token found in environment variables!")

# Whitelist domains (can be modified as needed)
WHITELISTED_DOMAINS = {
    'telegram.org',
    't.me',
    'telegram.me'
}

# Bot state (can be toggled by admins)
bot_active = True

# Rate limiting configuration (15 actions per minute)
CALLS_PER_MINUTE = 15

def extract_urls(text: str) -> list[str]:
    """Extract URLs from text using regex pattern matching."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    telegram_invite_pattern = r't\.me/(?:joinchat/)?[a-zA-Z0-9_-]+'
    
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    telegram_links = re.findall(telegram_invite_pattern, text, re.IGNORECASE)
    
    return list(set(urls + telegram_links))

def is_whitelisted(url: str) -> bool:
    """Check if the URL's domain is in the whitelist."""
    try:
        domain = validators.domain(url.split('/')[2])
        return domain in WHITELISTED_DOMAINS
    except:
        return False

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the group."""
    if not update.effective_chat:
        return False
    
    try:
        user = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )
        return user.status in ['creator', 'administrator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def admin_only(func):
    """Decorator to restrict commands to admins only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await is_admin(update, context):
            await update.message.reply_text("⚠️ This command is for administrators only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=60)
async def delete_message_with_rate_limit(chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Delete a message with rate limiting."""
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and check for links."""
    if not update.effective_message or not bot_active:
        return

    # Skip processing for admin messages
    if await is_admin(update, context):
        return

    message = update.effective_message
    text_to_check = message.text or message.caption or ""
    
    # Extract URLs from the message
    urls = extract_urls(text_to_check)
    
    if urls:
        # Check if any non-whitelisted URLs are present
        non_whitelisted = [url for url in urls if not is_whitelisted(url)]
        
        if non_whitelisted:
            # Log the deletion
            logger.info(
                f"Deleted message with links from user {update.effective_user.username or update.effective_user.id} "
                f"in chat {update.effective_chat.title or update.effective_chat.id}"
            )
            
            # Delete the message
            await delete_message_with_rate_limit(
                update.effective_chat.id,
                message.message_id,
                context
            )

@admin_only
async def toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle the bot's link deletion functionality."""
    global bot_active
    bot_active = not bot_active
    status = "activated" if bot_active else "deactivated"
    await update.message.reply_text(f"✅ Link deletion has been {status}.")

@admin_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the bot's current status."""
    status_text = "active" if bot_active else "inactive"
    await update.message.reply_text(
        f"🤖 Bot Status:\n"
        f"- Link deletion: {status_text}\n"
        f"- Whitelisted domains: {', '.join(WHITELISTED_DOMAINS)}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    await update.message.reply_text(
        "👋 Hello! I'm a link deletion bot. I will automatically delete messages "
        "containing links in this group.\n\n"
        "Admin commands:\n"
        "/toggle - Toggle link deletion on/off\n"
        "/status - Check bot status"
    )

def main() -> None:
    """Initialize and start the bot."""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("toggle", toggle_bot))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.CAPTION,
        handle_message
    ))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 