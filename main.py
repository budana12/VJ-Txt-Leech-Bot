import os
import tempfile
import shutil
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import cythonize_module  # We'll use the same helper module as before

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Pyrogram client configuration
app = Client(
    "py_to_so_bot",
    api_id=21705536,  # Replace with your API ID
    api_hash="c5bb241f6e3ecf33fe68a444e288de2d",  # Replace with your API hash
    bot_token="7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo"  # Replace with your bot token
)

# Start command handler
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "Hello! Send me a Python (.py) file and I will convert it to a .so shared object file.\n\n"
        "Note: The file should contain compilable Python code."
    )

# Help command handler
@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "Send me a Python (.py) file and I'll convert it to a .so shared object file.\n\n"
        "Conversion uses Cython. Ensure your code can be compiled.\n\n"
        "Limitations:\n"
        "- No dynamic imports\n"
        "- No eval/exec\n"
        "- Some Python features may not compile"
    )

# Document handler for .py files
@app.on_message(filters.document & (filters.regex(r'\.py$') | filters.regex(r'\.py$')))
async def process_py_file(client, message: Message):
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Check if the document has a file name
        if not message.document.file_name:
            await message.reply_text("The file doesn't have a name. Please send a properly named .py file.")
            return

        # Prepare file paths
        py_file_path = os.path.join(temp_dir, message.document.file_name)
        so_file_name = message.document.file_name.replace('.py', '.so')
        so_file_path = os.path.join(temp_dir, so_file_name)

        # Download the file
        await message.reply_text(f"Downloading {message.document.file_name}...")
        await client.download_media(message, file_name=py_file_path)

        # Convert to .so
        await message.reply_text(f"Converting {message.document.file_name} to .so...")
        try:
            cythonize_module.compile_py_to_so(py_file_path, so_file_path)

            # Check if conversion succeeded
            if os.path.exists(so_file_path):
                await message.reply_text("Conversion successful! Uploading the .so file...")
                await message.reply_document(
                    so_file_path,
                    caption="Here's your compiled .so file!"
                )
            else:
                await message.reply_text("Conversion failed. No .so file was created.")
        except Exception as e:
            await message.reply_text(f"Conversion failed: {str(e)}")
            logger.error(f"Conversion error: {str(e)}")

    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
        logger.error(f"Error processing file: {str(e)}")
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

# Error handler
@app.on_message(filters.all)
async def error_handler(client, message: Message):
    if message.document and not message.document.file_name.endswith('.py'):
        await message.reply_text("Please send a .py file for conversion.")

if __name__ == '__main__':
    app.run()
