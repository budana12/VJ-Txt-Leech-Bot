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

# Database to store user info
users_db = {}
reply_states = {}  # Store reply states separately

app = Client(
    "livegram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def clone_bot_features(new_token):
    """Function to clone all features to new bot"""
    try:
        new_client = Client(
            "cloned_bot_session",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=new_token,
            in_memory=True
        )
        
        await new_client.start()
        
        # Set up basic commands for the new bot
        await new_client.set_bot_commands([
            ("start", "Start the bot"),
            ("help", "Show help message"),
            ("broadcast", "Broadcast message (owner only)"),
            ("stats", "Show bot stats (owner only)"),
            ("clone", "Clone this bot (owner only)")
        ])
        
        bot_info = await new_client.get_me()
        await new_client.stop()
        return bot_info
    except Exception as e:
        logger.error(f"Error cloning bot: {e}")
        raise

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    users_db[user_id] = message.from_user.first_name
    
    welcome_text = (
        "🤖 **Welcome to LiveGram Bot**\n\n"
        "I can help you send and receive all types of Telegram messages.\n\n"
        "**Features:**\n"
        "- Send/receive text, photos, videos, documents, etc.\n"
        "- Broadcast messages to all users (owner only)\n"
        "- Clone bots using /clone command (owner only)\n\n"
        "Use /help to see available commands."
    )
    
    await message.reply_text(welcome_text)

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = (
        "🛠 **Available Commands**\n\n"
        "**For all users:**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "**For owner only:**\n"
        "/broadcast - Broadcast a message to all users\n"
        "/stats - Show bot statistics\n"
        "/clone - Clone this bot with a new token"
    )
    
    await message.reply_text(help_text)

# Stats command (owner only)
@app.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats(client: Client, message: Message):
    total_users = len(users_db)
    await message.reply_text(f"📊 **Bot Statistics**\n\nTotal Users: {total_users}")

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

# Clone command (owner only)
@app.on_message(filters.command("clone") & filters.private & filters.user(OWNER_ID))
async def clone_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /clone <new_bot_token>")
        return
    
    new_token = message.command[1]
    
    try:
        bot_info = await clone_bot_features(new_token)
        await message.reply_text(
            f"✅ Bot cloned successfully with all features!\n\n"
            f"New bot: @{bot_info.username}\n"
            f"Token: `{new_token}`"
        )
    except RPCError as e:
        await message.reply_text(f"❌ Failed to clone bot: {e}")

# Handle all incoming non-command messages
@app.on_message(filters.private & ~filters.command(["start", "help", "stats", "broadcast", "clone"]))
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        users_db[user_id] = message.from_user.first_name
    
    if user_id != OWNER_ID:
        try:
            forwarded = await message.forward(OWNER_ID)
            await client.send_message(
                OWNER_ID,
                f"📩 Message from {message.from_user.mention} (ID: {user_id})",
                reply_to_message_id=forwarded.id,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📤 Reply", callback_data=f"reply_{user_id}")
                ]])
            )
            await message.reply_text("✅ Your message has been sent to the bot admin!")
        except RPCError as e:
            await message.reply_text("❌ Failed to send your message. Please try again later.")
            logger.error(f"Failed to forward message: {e}")

# Handle callback queries
@app.on_callback_query(filters.regex("^reply_"))
async def reply_callback(client: Client, callback_query):
    owner_id = callback_query.from_user.id
    if owner_id != OWNER_ID:
        await callback_query.answer("You're not authorized to do this!", show_alert=True)
        return
    
    user_id = int(callback_query.data.split("_")[1])
    await callback_query.answer()
    
    # Store reply state with message ID to handle the response
    reply_states[callback_query.message.id] = user_id
    
    await callback_query.message.reply_text(
        f"💬 Enter your reply for user ID {user_id}:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel_reply_{callback_query.message.id}")
        ]])
    )

# Handle owner's replies
@app.on_message(filters.private & filters.user(OWNER_ID) & ~filters.command(["start", "help", "stats", "broadcast", "clone"]))
async def handle_owner_reply(client: Client, message: Message):
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.id
        if replied_msg_id in reply_states:
            user_id = reply_states[replied_msg_id]
            try:
                await message.copy(user_id)
                await message.reply_text("✅ Reply sent successfully!")
                del reply_states[replied_msg_id]
            except RPCError as e:
                await message.reply_text(f"❌ Failed to send reply: {e}")

# Handle cancel reply
@app.on_callback_query(filters.regex("^cancel_reply_"))
async def cancel_reply(client: Client, callback_query):
    msg_id = int(callback_query.data.split("_")[2])
    if msg_id in reply_states:
        del reply_states[msg_id]
    await callback_query.message.edit_text("🚫 Reply cancelled.")
    await callback_query.answer()

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()
