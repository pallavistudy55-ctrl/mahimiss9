import os
import logging
import telebot
import pymupdf
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8693410841:AAEHisYaRgRQpCrfqQ1AzTgwSMm2idi3ero")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID", "-1003493006883")
OWNER_ID = int(os.getenv("OWNER_ID", "6416451659"))

bot = telebot.TeleBot(BOT_TOKEN)

# Store custom thumbnail per user
CUSTOM_THUMB_PATH = "custom_thumb.jpg"

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    is_private = message.chat.type == "private"
    is_owner = message.from_user and message.from_user.id == OWNER_ID

    if is_private and is_owner:
        try:
            # Download highest resolution photo sent by owner
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(CUSTOM_THUMB_PATH, 'wb') as f:
                f.write(downloaded_file)
            
            # Resize image to square thumbnail (320x320 max)
            img = Image.open(CUSTOM_THUMB_PATH)
            img.thumbnail((320, 320))
            img.convert("RGB").save(CUSTOM_THUMB_PATH, "JPEG", quality=90)

            bot.reply_to(message, "✅ Custom Thumbnail saved! Ab jab bhi aap PDF bhejenge, yahi photo preview me dikhai degi.")
            logging.info("Saved custom thumbnail image.")
        except Exception as e:
            bot.reply_to(message, f"❌ Error saving photo: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    is_private = message.chat.type == "private"
    is_owner = message.from_user and message.from_user.id == OWNER_ID

    if is_private and is_owner:
        doc_file = message.document
        file_name = doc_file.file_name or "document.pdf"

        # Process PDF documents
        if file_name.lower().endswith('.pdf'):
            try:
                bot.reply_to(message, "⏳ PDF process ho raha hai aur Thumbnail ke saath send kiya ja raha hai...")
                
                # 1. Download PDF file
                file_info = bot.get_file(doc_file.file_id)
                pdf_data = bot.download_file(file_info.file_path)
                
                temp_pdf = "temp_input.pdf"
                with open(temp_pdf, 'wb') as f:
                    f.write(pdf_data)

                # 2. Determine Thumbnail
                thumb_path = "temp_thumb.jpg"
                if os.path.exists(CUSTOM_THUMB_PATH):
                    thumb_path = CUSTOM_THUMB_PATH
                else:
                    # Auto-extract Page 1 cover photo from PDF
                    pdf_doc = pymupdf.open(temp_pdf)
                    page1 = pdf_doc[0]
                    pix = page1.get_pixmap(dpi=100)
                    pix.save(thumb_path)
                    pdf_doc.close()
                    
                    # Resize thumbnail to <= 320px
                    img = Image.open(thumb_path)
                    img.thumbnail((320, 320))
                    img.convert("RGB").save(thumb_path, "JPEG", quality=90)

                caption = message.caption or ""

                # 3. Send PDF with Thumbnail to TARGET_CHAT_ID
                with open(temp_pdf, 'rb') as pdf_f, open(thumb_path, 'rb') as thumb_f:
                    bot.send_document(
                        chat_id=TARGET_CHAT_ID,
                        document=pdf_f,
                        thumbnail=thumb_f,
                        caption=caption
                    )
                
                # Also send back to user in Private Chat with Thumbnail
                with open(temp_pdf, 'rb') as pdf_f, open(thumb_path, 'rb') as thumb_f:
                    bot.send_document(
                        chat_id=message.chat.id,
                        document=pdf_f,
                        thumbnail=thumb_f,
                        caption="✅ **Thumbnail Preview Ready PDF!**\nIs file me bahar se cover photo dikhegi."
                    )

                logging.info(f"Successfully uploaded PDF {file_name} with thumbnail to {TARGET_CHAT_ID}")
                
                # Clean up temp pdf
                if os.path.exists(temp_pdf):
                    os.remove(temp_pdf)

            except Exception as e:
                logging.error(f"Failed to process PDF with thumbnail: {e}")
                bot.reply_to(message, f"❌ Error processing PDF: {e}")
        else:
            # Non-PDF documents: normal copy
            bot.copy_message(chat_id=TARGET_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)

@bot.message_handler(func=lambda message: True)
def process_message(message):
    is_private = message.chat.type == "private"
    is_owner = message.from_user and message.from_user.id == OWNER_ID

    if is_private and is_owner:
        try:
            bot.copy_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            logging.info(f"Successfully copied message {message.message_id} to {TARGET_CHAT_ID}")
        except Exception as e:
            logging.error(f"Failed to copy message {message.message_id}: {e}")

if __name__ == "__main__":
    logging.info("Telegram Copy & PDF Thumbnail Bot started listening...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.warning(f"Could not drop pending updates: {e}")
    bot.infinity_polling()
