import os
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import Message

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
ADMIN_ID = 1147534909  # Replace with your Telegram user ID

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                date_joined TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

init_db()

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
    /* All your existing CSS styles remain exactly the same */
    /* ... (keep all the CSS from previous version) ... */
  </style>
</head>
<body>
  <!-- All your existing HTML structure remains exactly the same -->
  <!-- ... (keep all the HTML from previous version) ... -->
</body>
</html>"""

# ---------- Database Functions ----------
def add_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, date_joined)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"Error adding user: {e}")
    finally:
        conn.close()

def get_total_users() -> int:
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        return count or 0
    except Exception as e:
        print(f"Error getting user count: {e}")
        return 0
    finally:
        conn.close()

def get_all_users() -> List[int]:
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        return users or []
    except Exception as e:
        print(f"Error getting user list: {e}")
        return []
    finally:
        conn.close()

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
