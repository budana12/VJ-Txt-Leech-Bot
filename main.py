import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
import logging
from pymongo import MongoClient

# -------------------- Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------- Config --------------------
API_ID = int(os.getenv("API_ID", "21705536"))
API_HASH = os.getenv("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo")
OWNER_ID = int(os.getenv("OWNER_ID", "5957208798"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# -------------------- MongoDB Setup --------------------
mongo = MongoClient(MONGO_URI)
db = mongo["livegram"]
users_col = db["users"]
forwarded_col = db["forwarded_map"]

# -------------------- Bot Factory --------------------
def create_bot(token: str, session_name: str = "livegram_bot"):
    return Client(
        session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=token,
        in_memory=True
    )

# -------------------- Handlers --------------------
def register_handlers(bot: Client):

    @bot.on_message(filters.command("start") & filters.private)
    async def start(_, message: Message):
        user_id = message.from_user.id
        users_col.update_one(
            {"_id": user_id},
            {"$set": {"first_name": message.from_user.first_name}},
            upsert=True
        )
        welcome_text = (
            "🤖 **Welcome to LiveGram Bot**\n\n"
            "I can help you send and receive Telegram messages.\n\n"
            "**Features:**\n"
            "- Receive all kinds of messages\n"
            "- Broadcast (owner only)\n"
            "- Clone this bot (/clone)\n\n"
            "Use /help to see all commands."
        )
        await message.reply_text(welcome_text)

    @bot.on_message(filters.command("help") & filters.private)
    async def help(_, message: Message):
        help_text = (
            "🛠 **Available Commands**\n\n"
            "**For everyone:**\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            "**For owner only:**\n"
            "/broadcast <text> - Send message to all users\n"
            "/stats - Show bot usage\n"
            "/clone <bot_token> - Clone bot"
        )
        await message.reply_text(help_text)

    @bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
    async def stats(_, message: Message):
        total = users_col.count_documents({})
        await message.reply_text(f"📊 Total users: {total}")

    @bot.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
    async def broadcast(_, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /broadcast <message>")
            return

        text = message.text.split(None, 1)[1]
        total, sent, failed = 0, 0, 0
        await message.reply("📢 Broadcasting...")

        for user in users_col.find({}):
            user_id = user["_id"]
            total += 1
            try:
                await bot.send_message(user_id, text)
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to {user_id}: {e}")
                failed += 1
            await asyncio.sleep(0.1)

        await message.reply(f"✅ Broadcast done.\nTotal: {total}\nSent: {sent}\nFailed: {failed}")

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
            info = await new_bot.get_me()
            await bot.send_message(OWNER_ID, f"✅ Cloned bot started: @{info.username}")
        except Exception as e:
            logger.error(f"Clone failed: {e}")
            await message.reply(f"❌ Clone failed: {e}")

    @bot.on_message(filters.private & ~filters.command(["start", "help", "stats", "broadcast", "clone"]))
    async def forward_to_owner(_, message: Message):
        user_id = message.from_user.id
        users_col.update_one(
            {"_id": user_id},
            {"$set": {"first_name": message.from_user.first_name}},
            upsert=True
        )

        if user_id != OWNER_ID:
            try:
                forwarded = await message.forward(OWNER_ID)
                forwarded_col.insert_one({
                    "_id": forwarded.id,
                    "user_id": user_id
                })
                # Silent forward
            except Exception as e:
                logger.error(f"Forward error: {e}")
                await message.reply("❌ Failed to send your message.")

    @bot.on_message(filters.private & filters.user(OWNER_ID))
    async def reply_from_owner(_, message: Message):
        if message.reply_to_message:
            record = forwarded_col.find_one({"_id": message.reply_to_message.message_id})
            if record:
                user_id = record["user_id"]
                try:
                    await message.copy(user_id)
                    await message.reply("✅ Reply sent.")
                except Exception as e:
                    logger.error(f"Reply failed: {e}")
                    await message.reply(f"❌ Failed to send reply: {e}")

# -------------------- Main --------------------
if __name__ == "__main__":
    logger.info("Starting LiveGram Bot with MongoDB...")
    bot = create_bot(BOT_TOKEN)
    register_handlers(bot)
    bot.run()
