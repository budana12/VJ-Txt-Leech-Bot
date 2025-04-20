import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = int(os.getenv("API_ID", "21705536"))  # Your API ID from my.telegram.org
API_HASH = os.getenv("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")  # Your API Hash from my.telegram.org
BOT_TOKEN = os.getenv("BOT_TOKEN", "7889175265:AAFzVLUGL58n5mh2z9Adap-EC634F4T_FVo")  # Your bot token from @BotFather
OWNER_ID = int(os.getenv("OWNER_ID", "5957208798"))  # Your user ID
# Database to store user info and chat states
users_db = {}
active_chats = {}  # {owner_msg_id: {"user_id": user_id, "user_msg_id": user_msg_id}}

app = Client(
    "livegram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# List of all commands to exclude from message handling
BOT_COMMANDS = ["start", "help", "clone", "broadcast", "stats"]

async def clone_bot(new_token):
    """Function to properly clone the bot"""
    try:
        # Create a new client with the new token
        new_client = Client(
            "cloned_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=new_token
        )
        
        # Start the new client to verify the token
        await new_client.start()
        bot_info = await new_client.get_me()
        
        # Set up basic commands for the new bot
        await new_client.set_bot_commands([
            ("start", "Start the bot"),
            ("help", "Show help message"),
            ("clone", "Clone this bot (owner only)"),
            ("broadcast", "Broadcast message (owner only)"),
            ("stats", "Show bot stats (owner only)")
        ])
        
        await new_client.stop()
        return bot_info
    except Exception as e:
        logger.error(f"Error cloning bot: {str(e)}")
        raise

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    users_db[user_id] = {
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "username": message.from_user.username
    }
    
    welcome_text = (
        "🤖 **Welcome to LiveGram Bot**\n\n"
        "You can chat with the bot owner through me.\n\n"
        "Just send any message and it will be forwarded to the owner.\n\n"
        "Use /help to see available commands."
    )
    
    await message.reply_text(welcome_text)

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = (
        "🛠 **Available Commands**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "**Owner Commands:**\n"
        "/clone - Clone this bot\n"
        "/broadcast - Broadcast message\n"
        "/stats - Show bot stats\n\n"
        "Just send any message to chat with the bot owner."
    )
    await message.reply_text(help_text)

# Handle all incoming messages from users (excluding commands)
@app.on_message(filters.private & ~filters.command(BOT_COMMANDS))
async def handle_user_message(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Store user info if not already in DB
    if user_id not in users_db:
        users_db[user_id] = {
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username
        }
    
    # Forward message to owner with reply button
    try:
        forwarded = await message.forward(OWNER_ID)
        active_chats[forwarded.id] = {
            "user_id": user_id,
            "user_msg_id": message.id
        }
        
        await client.send_message(
            OWNER_ID,
            f"📩 New message from {message.from_user.mention} (ID: {user_id})",
            reply_to_message_id=forwarded.id,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 Reply", callback_data=f"reply_{user_id}")
            ]])
        )
        
        await message.reply_text("✅ Your message has been sent to the bot owner!")
    except RPCError as e:
        await message.reply_text("❌ Failed to send your message. Please try again later.")
        logger.error(f"Failed to forward message: {e}")

# Handle owner's replies (when they reply to forwarded messages)
@app.on_message(filters.private & filters.user(OWNER_ID) & filters.reply)
async def handle_owner_reply(client: Client, message: Message):
    replied_msg = message.reply_to_message
    
    # Check if this is a reply to a forwarded user message
    if replied_msg and replied_msg.id in active_chats:
        chat_info = active_chats[replied_msg.id]
        user_id = chat_info["user_id"]
        
        try:
            # Send copy of owner's message to user
            await message.copy(user_id)
            await message.reply_text("✅ Reply sent to user!")
        except RPCError as e:
            await message.reply_text(f"❌ Failed to send reply: {e}")
            logger.error(f"Failed to send reply to user {user_id}: {e}")

# Clone command (owner only)
@app.on_message(filters.command("clone") & filters.private & filters.user(OWNER_ID))
async def clone_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /clone <new_bot_token>")
        return
    
    new_token = message.command[1]
    
    try:
        bot_info = await clone_bot(new_token)
        await message.reply_text(
            f"✅ Bot cloned successfully!\n\n"
            f"New bot: @{bot_info.username}\n"
            f"Token: `{new_token}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Failed to clone bot: {str(e)}")

# Broadcast command (owner only)
@app.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_text = message.text.split(None, 1)[1]
    total = 0
    successful = 0
    failed = 0
    
    await message.reply_text("📢 Starting broadcast...")
    
    for user_id in users_db:
        total += 1
        try:
            await client.send_message(user_id, broadcast_text)
            successful += 1
        except RPCError as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)
    
    await message.reply_text(
        f"📢 Broadcast completed!\n\n"
        f"Total users: {total}\n"
        f"Successful: {successful}\n"
        f"Failed: {failed}"
    )

# Stats command (owner only)
@app.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats(client: Client, message: Message):
    total_users = len(users_db)
    await message.reply_text(f"📊 **Bot Statistics**\n\nTotal Users: {total_users}")

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()
