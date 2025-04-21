import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 21705536  # Replace with your actual API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo"

bot = Client("py_to_so_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.private & filters.document)
async def py_to_so(client: Client, message: Message):
    doc = message.document

    if not doc.file_name.endswith(".py"):
        await message.reply("Please send a `.py` file only.")
        return

    # Download the file
    file_path = await message.download()
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    so_file = None

    # Create setup.py for Cython
    setup_content = f"""
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("{os.path.basename(file_path)}", compiler_directives={{'language_level': "3"}})
)
"""
    with open("setup.py", "w") as setup_file:
        setup_file.write(setup_content)

    try:
        # Compile the .py file to .so
        os.system("python3 setup.py build_ext --inplace")
        # Find the .so file
        for f in os.listdir("."):
            if f.startswith(base_name) and f.endswith(".so"):
                so_file = f
                break

        if so_file:
            await message.reply_document(so_file, caption="Here is your compiled .so file.")
        else:
            await message.reply("Compilation failed. Could not find the .so file.")
    except Exception as e:
        await message.reply(f"Error: {e}")

    # Cleanup
    for f in [file_path, "setup.py", so_file]:
        if f and os.path.exists(f):
            os.remove(f)
    os.system("rm -rf build")

bot.run()