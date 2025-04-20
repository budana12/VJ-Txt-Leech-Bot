from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

# Bot credentials from environment variables (Render compatible)
API_ID = int(os.environ.get("API_ID", 21705536))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo")

# Replace with your Telegram user ID (admin who will receive the messages)
ADMIN_ID = 5957208798

# Initialize bot client
bot = Client("livegram_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store mapping of message ID ↔ user ID
msg_store = {}

@bot.on_message(filters.private & ~filters.me)
async def user_message_handler(client: Client, message: Message):
    user = message.from_user
    # Forward the user's message to the admin
    fwd = await message.forward(ADMIN_ID)
    
    # Store original user ID using the forwarded message ID as key
    msg_store[fwd.id] = user.id

    # Optional: Notify the user
    await message.reply("📨 Your message has been sent to the admin.")


@bot.on_message(filters.user(ADMIN_ID) & filters.reply)
async def admin_reply_handler(client: Client, message: Message):
    reply_to = message.reply_to_message

    # Get the original user ID from the message store
    user_id = msg_store.get(reply_to.id)

    if not user_id:
        await message.reply("⚠️ User not found. The session might have expired.")
        return

    try:
        # Forward admin's reply to the user
        await message.copy(chat_id=user_id)
    except Exception as e:
        await message.reply(f"❌ Failed to send message: {e}")


print("🤖 Livegram bot is running...")
bot.run()
