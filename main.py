import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import logging
import asyncio
import pytz
from templates.html_template import generate_html

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAFyt61u6Zz5xXnJU5Sqt4x3_1aR7KaGogc"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
ADMIN_ID = 1147534909

# MongoDB Connection
MONGO_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.telegram_bot
    users_collection = db.users
    # Create index for user_id to ensure uniqueness
    users_collection.create_index("user_id", unique=True)
    logger.info("MongoDB connection established successfully")
except Exception as e:
    logger.error(f"MongoDB connection error: {e}")
    raise

# Initialize Telegram Bot
bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Utilities ----------
def sanitize_filename(name: str) -> str:
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url: str) -> str:
    """Modify specific URLs for compatibility."""
    if "classplusapp" in url:
        url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={url}"
    if "/master.mpd" in url:
        vid = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid}"
    return url

def extract_name_url(text: str) -> tuple:
    """Extract name and URL from text."""
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data) -> tuple:
    """Convert JSON data to collapsible HTML structure.
    Returns (html_content, total_items, total_links)
    """
    section_id = 0
    total_items = 0
    total_links = 0
    section_count = 0
    
    def recurse(obj, depth=0):
        nonlocal section_id, total_items, total_links, section_count
        html = ""
        if isinstance(obj, dict):
            for key, value in obj.items():
                section_id += 1
                section_count += 1
                inner = recurse(value, depth + 1)
                html += f"""
<div class="section">
  <button class="collapsible">{key}</button>
  <div class="content">{inner}</div>
</div>
"""
        elif isinstance(obj, list):
            for item in obj:
                html += recurse(item, depth)
        else:
            total_items += 1
            name, url = extract_name_url(str(obj))
            if url:
                total_links += 1
                html += f'<div class="item"><a href="{url}" target="_blank">{name}</a></div>\n'
            else:
                html += f"<div class='item'>{name}</div>\n"
        return html
    
    html_content = recurse(data)
    return html_content, total_items, total_links

# ---------- Database Functions ----------
def add_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
    """Add a user to the MongoDB database."""
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name, 
                    "last_name": last_name,
                    "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "$setOnInsert": {
                    "date_joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }, 
            upsert=True
        )
        logger.info(f"User {user_id} added/updated in database")
    except Exception as e:
        logger.error(f"Error adding user to MongoDB: {e}")

def get_total_users() -> int:
    """Get the total number of users from MongoDB."""
    try:
        return users_collection.count_documents({})
    except Exception as e:
        logger.error(f"Error getting user count from MongoDB: {e}")
        return 0

def get_all_users() -> List[int]:
    """Get a list of all user IDs from MongoDB."""
    try:
        users = users_collection.find({}, {"user_id": 1, "_id": 0})
        return [user["user_id"] for user in users]
    except Exception as e:
        logger.error(f"Error getting user list from MongoDB: {e}")
        return []

# ---------- Handlers ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle the /start command."""
    try:
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        await message.reply(
            "👋 Hi! Send me a JSON file and I'll convert it to a beautiful HTML file with collapsible sections.\n\n"
            "📌 Just upload any JSON file and I'll handle the rest!"
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """Handle the /stats command."""
    try:
        if message.from_user.id != ADMIN_ID:
            await message.reply("❌ You are not authorized to use this command.")
            return
            
        total_users = get_total_users()
        await message.reply(
            f"📊 Bot Statistics:\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📅 Last Updated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
        )
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply("❌ Error fetching statistics. Please try again later.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Handle the /broadcast command for admins."""
    try:
        if message.from_user.id != ADMIN_ID:
            await message.reply("❌ You are not authorized to use this command.")
            return
        
        if not message.reply_to_message:
            await message.reply("⚠️ Please reply to a message you want to broadcast.")
            return
        
        users = get_all_users()
        if not users:
            await message.reply("❌ No users found in database.")
            return
        
        total = len(users)
        success = 0
        failed = 0
        
        progress = await message.reply(f"📢 Broadcasting to {total} users...\n\n✅ Success: 0\n❌ Failed: 0")
        
        for user_id in users:
            try:
                await message.reply_to_message.copy(user_id)
                success += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send to {user_id}: {e}")
            
            if (success + failed) % 10 == 0 or (success + failed) == total:
                try:
                    await progress.edit_text(
                        f"📢 Broadcasting to {total} users...\n\n"
                        f"✅ Success: {success}\n"
                        f"❌ Failed: {failed}\n"
                        f"📊 Progress: {success + failed}/{total} ({((success + failed)/total)*100:.1f}%)"
                    )
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
        
        await progress.edit_text(
            f"📢 Broadcast completed!\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Total: {total} users"
        )
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply("❌ Error during broadcast. Please check logs.")

@bot.on_message(filters.document & filters.private)
async def handle_json(client: Client, message: Message):
    """Handle uploaded JSON documents."""
    path = None
    output_path = None
    try:
        # Add user to database
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        
        doc = message.document
        if not doc.file_name.endswith(".json"):
            await message.reply("❌ Please send a `.json` file.")
            return

        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/{sanitize_filename(doc.file_name)}"
        
        # Download file silently without any status message
        await message.download(path)
        logger.info(f"Downloaded file: {path}")
        
        # Process JSON file
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            await message.reply(f"❌ Invalid JSON format: {str(e)}")
            if os.path.exists(path):
                os.remove(path)
            return
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            await message.reply(f"❌ Error reading file: {str(e)}")
            if os.path.exists(path):
                os.remove(path)
            return
        
        # Generate HTML
        base_name = Path(doc.file_name).stem
        html_content, total_items, total_links = json_to_collapsible_html(data)
        html_code = generate_html(html_content, base_name, total_links, total_items)
        output_path = f"downloads/{base_name}.html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_code)
        
        logger.info(f"HTML file generated: {output_path}")

        # Format the caption with user details and IST timestamp
        user = message.from_user
        india_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        timestamp = india_time.strftime('%Y-%m-%d | ⏰ %H:%M:%S')
        
        caption = f"""📖 𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 : {base_name}

👤 User: {user.first_name or ''} {user.last_name or ''}
🆔 ID: <code>{user.id}</code>"""
        if user.username:
            caption += f"\n👤 Username: @{user.username}"
        caption += f"\n📅 {timestamp} (this is time of extraction it means constant)"
        
        # Forward JSON and HTML to the channel
        channel_id = "kuvnypkyjk"
        
        try:
            # First send to user
            await message.reply_document(
                document=output_path,
                caption=f"✅ HTML generated for **{base_name}**",
                thumb="thumbnail.jpg"
            )
            
            # Then forward to channel
            try:
                # Forward JSON file to channel
                await client.send_document(
                    chat_id=f"@{channel_id}",
                    document=path,
                    caption=caption
                )
                
                # Forward HTML file to channel
                await client.send_document(
                    chat_id=f"@{channel_id}",
                    document=output_path,
                    caption=caption,
                    thumb="thumbnail.jpg"
                )
            except Exception as e:
                logger.error(f"Error forwarding to channel: {e}")
                
        except Exception as e:
            logger.error(f"Error sending document: {e}")
            # Try without thumbnail if it fails
            try:
                await message.reply_document(
                    document=output_path,
                    caption=f"✅ HTML generated for **{base_name}**"
                )
            except Exception as e2:
                logger.error(f"Error sending document without thumbnail: {e2}")
                await message.reply("❌ Error sending the generated HTML file.")
        
    except Exception as e:
        logger.error(f"Error handling JSON: {e}")
        await message.reply("❌ An error occurred while processing your file. Please try again.")
    finally:
        # Clean up files - but only after we've sent them to the channel
        try:
            # We'll keep copies of the files in downloads directory
            # but not remove them after sending to allow archiving
            logger.info("Files processed successfully")
        except Exception as e:
            logger.error(f"Error during file processing: {e}")

# ---------- Start Bot ----------
# Define a Flask app within the same file for web application
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Engineers Babu API is running"})

if __name__ == "__main__":
    logger.info("🤖 Bot is starting...")
    try:
        bot.run()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        mongo_client.close()
        logger.info("Bot stopped")
