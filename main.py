import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
import logging

# -------------------- Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------- Config --------------------
API_ID = int(os.getenv("API_ID", "21705536"))  # Your API ID from my.telegram.org
API_HASH = os.getenv("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")  # Your API Hash from my.telegram.org
BOT_TOKEN = os.getenv("BOT_TOKEN", "7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo")  # Your bot token from @BotFather
OWNER_ID = int(os.getenv("OWNER_ID", "5957208798"))  # Your user ID
# In-memory user database and forward mapping
users_db = {}
forwarded_map = {}  # Maps forwarded_msg_id -> original_user_id

# -------------------- Bot Factory --------------------
def create_bot(token: str, session_name: str = "livegram_bot"):
    return Client(
        session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=token,
        in_memory=True
    )

# -------------------- Handler Registration --------------------
def register_handlers(bot: Client):

    @bot.on_message(filters.command("start") & filters.private)
    async def start(_, message: Message):
        user_id = message.from_user.id
        users_db[user_id] = message.from_user.first_name
        welcome = (
            "🤖 **Welcome to LiveGram Bot**\n\n"
            "I can help you send and receive all types of Telegram messages.\n\n"
            "**Features:**\n"
            "- Send/receive text, photos, videos, etc.\n"
            "- Broadcast to all users (owner only)\n"
            "- Clone me using /clone (owner only)\n\n"
            "Use /help to see available commands."
        )
        await message.reply_text(welcome)

    @bot.on_message(filters.command("help") & filters.private)
    async def help_command(_, message: Message):
        help_text = (
            "🛠 **Available Commands**\n\n"
            "**For all users:**\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            "**For owner only:**\n"
            "/broadcast <msg> - Send message to all users\n"
            "/stats - Show user count\n"
            "/clone <token> - Clone bot"
        )
        await message.reply_text(help_text)

    @bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
    async def stats(_, message: Message):
        total_users = len(users_db)
        await message.reply_text(f"📊 **Bot Stats**\n\nTotal users: {total_users}")

    @bot.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
    async def broadcast(_, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /broadcast <message>")
            return
        text = message.text.split(None, 1)[1]
        total, success, failed = 0, 0, 0

        await message.reply("📢 Broadcasting...")

        for uid in users_db:
            total += 1
            try:
                await bot.send_message(uid, text)
                success += 1
            except Exception as e:
                logger.warning(f"Failed to send to {uid}: {e}")
                failed += 1
            await asyncio.sleep(0.1)

        await message.reply(
            f"✅ Broadcast complete.\n\n"
            f"Total: {total}\nSent: {success}\nFailed: {failed}"
        )

    @bot.on_message(filters.command("clone") & filters.private & filters.user(OWNER_ID))
    async def clone(_, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /clone <new_bot_token>")
            return
        new_token = message.command[1]
        try:
            new_bot = create_bot(new_token, session_name="cloned_bot")
            register_handlers(new_bot)
            await new_bot.start()
            bot_info = await new_bot.get_me()
            await bot.send_message(OWNER_ID, f"✅ Cloned bot started: @{bot_info.username}")
        except Exception as e:
            await message.reply(f"❌ Failed to clone bot: {e}")

    @bot.on_message(filters.private & ~filters.command(["start", "help", "stats", "broadcast", "clone"]))
    async def handle_user(_, message: Message):
        uid = message.from_user.id
        if uid not in users_db:
            users_db[uid] = message.from_user.first_name
        if uid != OWNER_ID:
            try:
                forwarded = await message.forward(OWNER_ID)
                forwarded_map[forwarded.id] = uid
                # No message sent to user (silent)
            except Exception as e:
                logger.error(f"Forward failed: {e}")
                await message.reply("❌ Couldn't forward message.")

    @bot.on_message(filters.private & filters.user(OWNER_ID))
    async def owner_reply(_, message: Message):
        if message.reply_to_message and message.reply_to_message.message_id in forwarded_map:
            user_id = forwarded_map[message.reply_to_message.message_id]
            try:
                await message.copy(user_id)
                await message.reply("✅ Reply sent.")
            except Exception as e:
                logger.error(f"Reply failed: {e}")
                await message.reply(f"❌ Reply failed: {e}")

# -------------------- Main --------------------
if __name__ == "__main__":
    logger.info("Starting main bot...")
    main_bot = create_bot(BOT_TOKEN)
    register_handlers(main_bot)
    main_bot.run()
