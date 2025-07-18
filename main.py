#!/usr/bin/env python3
"""
UPSC Vault Telegram Bot
A production-grade bot for organizing and delivering UPSC study content.
"""

import logging
import asyncio
import sys
import time
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, ADMIN_ID
from database import DatabaseManager
from bot_handlers import BotHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to start the bot."""
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Initialize database
            db_manager = DatabaseManager()
            db_manager.init_database()

            # Initialize bot handlers
            bot_handlers = BotHandlers(db_manager)

            # Create application with better error handling
            application = Application.builder().token(BOT_TOKEN).build()

            # Add error handler
            async def error_handler(update, context):
                """Log errors and handle conflicts."""
                error = context.error
                if "Conflict" in str(
                        error) or "terminated by other getUpdates" in str(
                            error):
                    logger.warning(
                        "Conflict detected during update processing")
                    return
                logger.error(f"Update {update} caused error {error}")

            application.add_error_handler(error_handler)

            # Add handlers
            application.add_handler(
                CommandHandler("start", bot_handlers.start_command))
            application.add_handler(
                CallbackQueryHandler(bot_handlers.button_callback))
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot_handlers.handle_text_message))

            # Start the bot with better polling configuration
            logger.info("Starting UPSC Vault Bot...")

            # Run with conflict-resistant settings
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
                close_loop=False,
                timeout=30,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30)

        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in
                   ["conflict", "terminated by other getupdates", "409"]):
                retry_count += 1
                wait_time = min(10 * retry_count,
                                60)  # Exponential backoff, max 60 seconds
                logger.warning(
                    f"Bot conflict detected (attempt {retry_count}/{max_retries}), waiting {wait_time} seconds before retry..."
                )
                time.sleep(wait_time)
                continue
            elif any(keyword in error_str
                     for keyword in ["network", "timeout", "connection"]):
                retry_count += 1
                wait_time = 5
                logger.warning(
                    f"Network error detected (attempt {retry_count}/{max_retries}), waiting {wait_time} seconds before retry..."
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Failed to start bot: {e}")
                retry_count += 1
                time.sleep(5)
                continue

    logger.error(
        f"Maximum retry attempts ({max_retries}) reached. Bot shutting down.")
    sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
