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
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
ADMIN_ID = 1147534909  # Replace with your Telegram user ID
MONGO_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URI

# Initialize MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["json_to_html_bot"]
    users_collection = db["users"]
    users_collection.create_index("user_id", unique=True)
except PyMongoError as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Utilities ----------
def sanitize_filename(name: str) -> str:
    """Sanitize filename to remove invalid characters."""
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url: str) -> str:
    """Modify specific URLs to work with custom players."""
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

def json_to_collapsible_html(data) -> str:
    """Convert JSON data to HTML with collapsible sections."""
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
    """Generate complete HTML document from JSON data."""
    display_title = title.replace("_", " ")
    content_html = json_to_collapsible_html(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
    }}
    h1 {{
      color: #2c3e50;
      text-align: center;
      margin-bottom: 30px;
    }}
    .section {{
      margin-bottom: 10px;
    }}
    .collapsible {{
      background-color: #3498db;
      color: white;
      cursor: pointer;
      padding: 12px;
      width: 100%;
      border: none;
      text-align: left;
      outline: none;
      font-size: 16px;
      border-radius: 4px;
      margin: 5px 0;
      transition: background-color 0.3s;
    }}
    .collapsible:hover {{
      background-color: #2980b9;
    }}
    .content {{
      padding: 0 18px;
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.2s ease-out;
      background-color: #f9f9f9;
      border-radius: 0 0 4px 4px;
    }}
    .item {{
      padding: 10px;
      background-color: white;
      margin: 5px 0;
      border-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .item a {{
      color: #3498db;
      text-decoration: none;
    }}
    .item a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <h1>{display_title}</h1>
  <div class="container">
    {content_html}
  </div>
  <script>
    document.querySelectorAll('.collapsible').forEach(button => {{
      button.addEventListener('click', function() {{
        this.classList.toggle('active');
        const content = this.nextElementSibling;
        if (content.style.maxHeight) {{
          content.style.maxHeight = null;
        }} else {{
          content.style.maxHeight = content.scrollHeight + 'px';
        }} 
      }});
    }});
  </script>
</body>
</html>"""

# ---------- Database Functions ----------
def add_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> bool:
    """Add user to MongoDB if not exists."""
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "date_joined": datetime.now(),
                "last_seen": datetime.now()
            }},
            upsert=True
        )
        return True
    except PyMongoError as e:
        print(f"Error adding user: {e}")
        return False

def update_user_activity(user_id: int) -> bool:
    """Update user's last seen timestamp."""
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_seen": datetime.now()}}
        )
        return True
    except PyMongoError as e:
        print(f"Error updating user activity: {e}")
        return False

def get_total_users() -> int:
    """Get total number of users."""
    try:
        return users_collection.count_documents({})
    except PyMongoError as e:
        print(f"Error getting user count: {e}")
        return 0

def get_all_users() -> List[int]:
    """Get list of all user IDs."""
    try:
        return [user["user_id"] for user in users_collection.find({}, {"user_id": 1})]
    except PyMongoError as e:
        print(f"Error getting user list: {e}")
        return []

# ---------- Handlers ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command."""
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
    """Handle /stats command (admin only)."""
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
        print(f"Error in stats command: {e}")
        await message.reply("❌ Error fetching statistics. Please try again later.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Handle /broadcast command (admin only)."""
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
    """Handle JSON file uploads."""
    try:
        # Update user activity
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        
        doc = message.document
        if not doc.file_name.endswith(".json"):
            await message.reply("❌ Please send a `.json` file.")
            return

        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/{sanitize_filename(doc.file_name)}"
        
        status_msg = await message.reply("📥 Downloading your file...")
        await message.download(path)
        
        await status_msg.edit_text("🔍 Processing JSON file...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            await status_msg.edit_text(f"❌ Error reading JSON: {str(e)}")
            os.remove(path)
            return
        
        base_name = Path(doc.file_name).stem
        await status_msg.edit_text("🛠 Generating HTML...")
        html_code = generate_html(data, base_name)
        output_path = f"downloads/{base_name}.html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_code)

        await status_msg.edit_text("📤 Uploading HTML file...")
        await message.reply_document(
            document=output_path,
            caption=f"✅ HTML generated for **{base_name}**",
            thumb=THUMBNAIL_URL
        )
        
        os.remove(path)
        os.remove(output_path)
        await status_msg.delete()
    except Exception as e:
        print(f"Error handling JSON: {e}")
        await message.reply("❌ An error occurred while processing your file. Please try again.")
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
        try:
            mongo_client.close()
        except:
            pass
