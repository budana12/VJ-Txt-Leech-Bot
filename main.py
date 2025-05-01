import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAFyt61u6Zz5xXnJU5Sqt4x3_1aR7KaGogc"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
ADMIN_ID = 1147534909  # Replace with your Telegram user ID
MONGO_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.get_database("json_to_html_bot")
    users_collection = db.users
    print("✅ Connected to MongoDB")
except PyMongoError as e:
    print(f"❌ MongoDB connection error: {e}")
    raise

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Utilities ----------
def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url: str) -> str:
    if "classplusapp" in url:
        url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={url}"
    if "/master.mpd" in url:
        vid = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid}"
    return url

def extract_name_url(text: str) -> tuple:
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data) -> str:
    section_id = 0
    def recurse(obj, depth=0):
        nonlocal section_id
        html = ""
        if isinstance(obj, dict):
            for key, value in obj.items():
                section_id += 1
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
            name, url = extract_name_url(str(obj))
            if url:
                html += f'<div class="item"><a href="{url}" target="_blank">{name}</a></div>\n'
            else:
                html += f"<div class='item'>{name}</div>\n"
        return html
    return recurse(data)

def generate_html(data, title: str) -> str:
    display_title = title.replace("_", " ")
    content_html = json_to_collapsible_html(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    /* All CSS styles remain exactly the same as before */
    /* ... (previous CSS content) ... */
  </style>
</head>
<body>
  <!-- All HTML structure remains exactly the same as before -->
  <!-- ... (previous HTML content) ... -->
</body>
</html>"""

# ---------- Database Functions ----------
def add_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "date_joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }},
            upsert=True
        )
    except PyMongoError as e:
        print(f"Error adding user: {e}")

def get_total_users() -> int:
    try:
        return users_collection.count_documents({})
    except PyMongoError as e:
        print(f"Error getting user count: {e}")
        return 0

def get_all_users() -> List[int]:
    try:
        return [user["user_id"] for user in users_collection.find({}, {"user_id": 1})]
    except PyMongoError as e:
        print(f"Error getting user list: {e}")
        return []

# ---------- Handlers ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    try:
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        await message.reply(
            "👋 Hi! Send me a JSON file and I'll convert it to a beautiful HTML file with collapsible sections.\n\n"
            "📌 Just upload any JSON file and I'll handle the rest!"
        )
    except Exception as e:
        print(f"Error in start command: {e}")

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    try:
        total_users = get_total_users()
        await message.reply(
            f"📊 Bot Statistics:\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📅 Last Updated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
        )
    except Exception as e:
        print(f"Error in stats command: {e}")
        await message.reply("❌ Error fetching statistics. Please try again later.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
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
                print(f"Failed to send to {user_id}: {e}")
            
            if (success + failed) % 10 == 0 or (success + failed) == total:
                try:
                    await progress.edit_text(
                        f"📢 Broadcasting to {total} users...\n\n"
                        f"✅ Success: {success}\n"
                        f"❌ Failed: {failed}\n"
                        f"📊 Progress: {success + failed}/{total} ({((success + failed)/total)*100:.1f}%)"
                    )
                except Exception as e:
                    print(f"Error updating progress: {e}")
        
        await progress.edit_text(
            f"📢 Broadcast completed!\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Total: {total} users"
        )
    except Exception as e:
        print(f"Error in broadcast command: {e}")
        await message.reply("❌ Error during broadcast. Please check logs.")

@bot.on_message(filters.document & filters.private)
async def handle_json(client: Client, message: Message):
    try:
        # Add user to database
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        
        doc = message.document
        if not doc.file_name.endswith(".json"):
            return

        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/{sanitize_filename(doc.file_name)}"
        
        # Download file silently
        await message.download(path)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            os.remove(path)
            return
        
        base_name = Path(doc.file_name).stem
        html_code = generate_html(data, base_name)
        output_path = f"downloads/{base_name}.html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_code)

        # Send the HTML file silently
        await client.send_document(
            chat_id=message.chat.id,
            document=output_path,
            caption=f"✅ HTML generated for **{base_name}**",
            thumb=THUMBNAIL_URL
        )
        
        # Clean up files
        os.remove(path)
        os.remove(output_path)
        
    except Exception as e:
        print(f"Error handling JSON: {e}")
        if 'path' in locals() and os.path.exists(path):
            os.remove(path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

# ---------- Start Bot ----------
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    try:
        bot.run()
    except Exception as e:
        print(f"Bot crashed: {e}")
    finally:
        print("Bot stopped")
        if 'mongo_client' in locals():
            mongo_client.close()
