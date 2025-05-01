import os
import re
import json
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pathlib import Path
import pytz

# ========== BOT CONFIG ==============
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
OWNER_ID = 5021644377
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
FORWARD_CHANNEL = "@kuvnypkyjk"

MONGO_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["json_to_html_bot"]
users_col = db["users"]

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ========== UTILS ==============
def sanitize_filename(name):
    """Sanitize filename by replacing invalid characters with underscores."""
    return re.sub(r'[<>:"/\\|?*\0-\x1f]', '_', name).strip()

def modify_url(url: str) -> str:
    """Modify URLs to use custom extractors when applicable."""
    if not url:
        return url
        
    if "classplusapp" in url:
        clean_url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={clean_url}"
    elif "/master.mpd" in url:
        vid_id = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid_id}"
    return url

def extract_name_url(text: str):
    """Extract name and URL from a string."""
    if not isinstance(text, str):
        return str(text), None
        
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data):
    """Convert JSON data to collapsible HTML structure."""
    section_id = 0
    
    def recurse(obj, depth=0):
        nonlocal section_id
        html = ""
        
        if isinstance(obj, dict):
            if "resource" in obj and isinstance(obj["resource"], dict):
                resource = obj["resource"]
                title = resource.get("title", "Untitled")
                url = resource.get("url")
                if url:
                    html += f'<div class="item"><a href="{modify_url(url)}" target="_blank">{title}</a></div>\n'
                else:
                    html += f"<div class='item'>{title}</div>\n"
            else:
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
            if all(isinstance(i, (str, int, float)) for i in obj):
                html += "<div class='item'>" + ", ".join(map(str, obj)) + "</div>\n"
            else:
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

def generate_html(json_data, original_name, user):
    """Generate complete HTML file from JSON data."""
    try:
        display_title = original_name.replace("_", " ")
        formatted_datetime = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("📅 %d-%m-%Y ⏰ %I:%M %p")
        html_body = json_to_collapsible_html(json_data)
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None"
        username = f"@{user.username}" if user.username else "🚫 None"

        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #f3f3f3; }}
    .container {{ width: 800px; margin: 30px auto; }}
    .loading-wrapper {{ text-align: center; padding: 20px; background: #000; color: #fff; }}
    .loading-text {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
    .progress-bar {{ background: #444; border-radius: 20px; height: 20px; overflow: hidden; }}
    .progress-bar-fill {{ height: 100%; width: 100%; background: linear-gradient(90deg, red, orange, yellow, green, blue, indigo, violet); animation: load 3s ease-in-out infinite; }}
    @keyframes load {{ 0% {{width: 0;}} 100% {{width: 100%;}} }}
    .header {{ text-align: center; background: linear-gradient(135deg, #007BFF, #00C6FF); padding: 20px; border-radius: 15px; color: white; }}
    .thumbnail {{ width: 120px; border-radius: 10px; }}
    .collapsible {{ background-color: #007BFF; color: white; cursor: pointer; padding: 10px; width: 100%; border: none; outline: none; font-size: 16px; border-radius: 5px; margin-top: 10px; }}
    .active, .collapsible:hover {{ background-color: #0056b3; }}
    .content {{ padding: 10px 18px; display: none; overflow: hidden; background-color: #fff; border-radius: 5px; }}
    .section {{ border: 1px solid #ddd; border-radius: 4px; margin-bottom: 8px; padding: 5px; }}
    .item {{ padding: 8px; border-bottom: 1px solid #ccc; text-align: center; }}
    .footer-strip {{ margin-top: 40px; padding: 10px; text-align: center; background: linear-gradient(to right, #ff6a00, #ee0979); color: white; font-weight: bold; border-radius: 8px; }}
    p, .datetime {{ text-align: center; }}
  </style>
</head>
<body>
  <div class="loading-wrapper">
    <div class="loading-text">Welcome To Engineer's Babu</div>
    <div class="progress-bar">
        <div class="progress-bar-fill"></div>
    </div>
    <div>Your Content is preparing...</div>
  </div>

  <div class="container" id="main-content" style="display:none">
    <div class="header">
      <img class="thumbnail" src="{THUMBNAIL_URL}" alt="Thumbnail">
      <h1>{display_title}</h1>
    </div>
    <p class="datetime">{formatted_datetime} (IST)</p>
    <p>♦️Use This Bot for JSON to HTML File Extraction : <a href="https://t.me/htmlextractorbot" target="_blank">@htmlextractorbot</a></p>
    {html_body}
    <button class="collapsible">👤 View User Details</button>
    <div class="content">
        <div class="item">🆔 User ID: {user.id}</div>
        <div class="item">👤 Username: {username}</div>
        <div class="item">📛 Full Name: {full_name}</div>
        <div class="item">💎 Premium: {'✨ Yes' if user.is_premium else '❌ No'}</div>
        <div class="item">🤖 Bot: {'✅ Yes' if user.is_bot else '❌ No'}</div>
    </div>
    <div class="footer-strip">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</div>
  </div>

<script>
window.addEventListener("load", () => {{
  document.querySelector(".loading-wrapper").style.display = "none";
  document.getElementById("main-content").style.display = "block";
}});
const collapsibles = document.getElementsByClassName("collapsible");
for (let i = 0; i < collapsibles.length; i++) {{
  collapsibles[i].addEventListener("click", function () {{
    this.classList.toggle("active");
    const content = this.nextElementSibling;
    if (content.style.display === "block") {{
      content.style.display = "none";
    }} else {{
      content.style.display = "block";
    }}
  }});
}}
</script>
</body>
</html>'''
        return html_template
    except Exception as e:
        print(f"Error generating HTML: {e}")
        raise

# ========== HANDLER ==============
@bot.on_message(filters.document & filters.private)
async def handle_json_file(client: Client, message: Message):
    try:
        user = message.from_user
        if not user:
            await message.reply("❌ Cannot identify user.")
            return

        users_col.update_one(
            {"_id": user.id},
            {"$set": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "last_used": datetime.now()
            }},
            upsert=True
        )

        doc = message.document
        if not doc.file_name.lower().endswith(".json"):
            await message.reply("❌ Please send a valid `.json` file.")
            return

        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{sanitize_filename(doc.file_name)}"
        await message.download(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            await message.reply(f"❌ Invalid JSON format: {e}")
            os.remove(file_path)
            return
        except Exception as e:
            await message.reply(f"❌ Error reading file: {e}")
            os.remove(file_path)
            return

        base_name = Path(doc.file_name).stem
        output_file = f"downloads/{base_name}.html"
        
        try:
            html = generate_html(data, base_name, user)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            await message.reply(f"❌ Error generating HTML: {e}")
            os.remove(file_path)
            return

        await message.reply_document(
            document=output_file,
            caption=f"📖 𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 : {base_name}\n🔗 𝐓𝐨𝐭𝐚𝐥 𝐋𝐢𝐧𝐤𝐬: {len(data)}\n👤 User: {user.first_name or ''} {user.last_name or ''}\n🆔 ID: <code>{user.id}</code>",
            quote=True
        )

        if FORWARD_CHANNEL:
            try:
                await client.send_document(
                    FORWARD_CHANNEL, 
                    output_file, 
                    caption=f"📁 Generated HTML for {base_name} by {user.id} (@{user.username})"
                )
                await client.send_document(
                    FORWARD_CHANNEL, 
                    file_path, 
                    caption=f"📄 Original JSON: {doc.file_name}"
                )
            except Exception as e:
                print(f"Error forwarding files: {e}")

        os.remove(file_path)
        os.remove(output_file)

    except Exception as e:
        await message.reply(f"❌ An unexpected error occurred: {e}")
        print(f"Error in handle_json_file: {e}")

@bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats(client: Client, message: Message):
    try:
        total_users = users_col.count_documents({})
        active_users = users_col.count_documents({"last_used": {"$gte": datetime.now() - timedelta(days=30)}})
        await message.reply_text(
            f"📊 Bot Statistics:\n\n"
            f"• Total users: {total_users}\n"
            f"• Active users (last 30 days): {active_users}"
        )
    except Exception as e:
        await message.reply(f"❌ Error fetching stats: {e}")

@bot.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
async def broadcast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message>")
        return

    text = message.text.split(None, 1)[1]
    total, sent, failed = 0, 0, 0
    progress_msg = await message.reply("📢 Broadcasting... Please wait")

    try:
        async for user in users_col.find({}):
            user_id = user["_id"]
            total += 1
            try:
                await client.send_message(user_id, text)
                sent += 1
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")
                failed += 1
            
            if total % 10 == 0:
                await progress_msg.edit_text(
                    f"📢 Broadcasting...\n\n"
                    f"• Total: {total}\n"
                    f"• Sent: {sent}\n"
                    f"• Failed: {failed}"
                )
            await asyncio.sleep(0.1)

        await progress_msg.edit_text(
            f"✅ Broadcast completed!\n\n"
            f"• Total users: {total}\n"
            f"• Successfully sent: {sent}\n"
            f"• Failed: {failed}"
        )
    except Exception as e:
        await message.reply(f"❌ Broadcast failed: {e}")

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    try:
        bot.run()
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
