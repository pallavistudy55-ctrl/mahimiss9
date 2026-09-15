import os
import logging
import telebot

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables (with fallback defaults from n8n workflow)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8693410841:AAEHisYaRgRQpCrfqQ1AzTgwSMm2idi3ero")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID", "-1003493006883")
OWNER_ID = int(os.getenv("OWNER_ID", "6416451659"))

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def process_message(message):
    # Filter: Only Private Messages AND from Owner ID
    is_private = message.chat.type == "private"
    is_owner = message.from_user and message.from_user.id == OWNER_ID

    if is_private and is_owner:
        try:
            bot.copy_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            logging.info(f"Successfully copied message {message.message_id} to group {TARGET_CHAT_ID}")
        except Exception as e:
            logging.error(f"Failed to copy message {message.message_id}: {e}")

if __name__ == "__main__":
    logging.info("Telegram Copy Bot started listening...")
    bot.infinity_polling(skip_pending_updates=True)
