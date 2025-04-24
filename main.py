import os
import tempfile
import shutil
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import cythonize_module

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hello! Send me a Python (.py) file and I will convert it to a .so shared object file for you.\n\n'
        'Note: The file should contain compilable Python code.'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Send me a Python (.py) file and I will convert it to a .so shared object file.\n\n'
        'The conversion is done using Cython. Make sure your code can be compiled.\n\n'
        'Limitations:\n'
        '- No dynamic imports\n'
        '- No eval/exec\n'
        '- Some Python features may not be supported'
    )

def process_py_file(update: Update, context: CallbackContext) -> None:
    """Process the received .py file and convert it to .so"""
    if not update.message.document:
        update.message.reply_text("Please send a .py file as a document.")
        return
    
    file = update.message.document
    if not file.file_name.endswith('.py'):
        update.message.reply_text("Please send a file with .py extension.")
        return
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Download the file
        py_file_path = os.path.join(temp_dir, file.file_name)
        so_file_name = file.file_name.replace('.py', '.so')
        so_file_path = os.path.join(temp_dir, so_file_name)
        
        # Get the file from Telegram
        file_obj = context.bot.get_file(file.file_id)
        file_obj.download(py_file_path)
        
        # Notify user
        update.message.reply_text(f"File received. Starting conversion of {file.file_name}...")
        
        # Convert to .so using Cython
        try:
            cythonize_module.compile_py_to_so(py_file_path, so_file_path)
            
            # Check if .so file was created
            if os.path.exists(so_file_path):
                with open(so_file_path, 'rb') as f:
                    update.message.reply_document(
                        document=InputFile(f, filename=so_file_name),
                        caption="Here's your compiled .so file!"
                    )
            else:
                update.message.reply_text("Conversion failed. No .so file was created.")
        except Exception as e:
            update.message.reply_text(f"Conversion failed: {str(e)}")
            logger.error(f"Conversion error: {str(e)}")
            
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")
        logger.error(f"Error processing file: {str(e)}")
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.error(f'Update {update} caused error {context.error}')
    if update and update.message:
        update.message.reply_text('An error occurred while processing your request.')

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Document handler for .py files
    dispatcher.add_handler(MessageHandler(Filters.document & Filters.document.mime_type("text/x-python"), process_py_file))

    # Error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
