import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import pytz

# Bot Configuration
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
OWNER_ID = 1147534909  # Replace with your ID
MONGO_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize bot and database
bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["json_to_html_bot"]
users_col = db["users"]

# Utility Functions
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url: str) -> str:
    if "classplusapp" in url:
        clean_url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={clean_url}"
    elif "/master.mpd" in url:
        vid_id = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid_id}"
    return url

def extract_name_url(text: str):
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data):
    section_id = 0

    def recurse(obj, depth=0):
        nonlocal section_id
        html = ""
        if isinstance(obj, dict):
            for key, value in obj.items():
                section_id += 1
                inner = recurse(value, depth + 1)
                html += f"""
<div class=\"section\">
  <button class=\"collapsible\">{key}</button>
  <div class=\"content\">{inner}</div>
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

def generate_html(json_data, original_name):
    display_title = original_name.replace("_", " ")
    formatted_datetime = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("📅 %d-%m-%Y | ⏰ %I:%M:%S %p")
    html_body = json_to_collapsible_html(json_data)

    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>{display_title}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; margin: 0; }}
    .loading-wrapper {{ text-align: center; padding: 50px 0; }}
    .loading-text {{ font-size: 32px; color: #007BFF; margin-bottom: 20px; }}
    .progress-bar {{ width: 60%; height: 10px; margin: auto; background: #ddd; border-radius: 10px; overflow: hidden; }}
    .progress-bar-fill {{ width: 100%; height: 100%; background: linear-gradient(270deg, #00C6FF, #007BFF, #7EE8FA); animation: load 2s infinite; }}
    @keyframes load {{ 0% {{transform: translateX(-100%)}} 100% {{transform: translateX(100%)}} }}
    .container {{ width: 800px; margin: 20px auto; }}
    .header {{ display: flex; align-items: center; gap: 20px; justify-content: center; text-align: center; background: linear-gradient(135deg, #007BFF, #00C6FF, #7EE8FA); padding: 20px; border-radius: 15px; }}
    .thumbnail {{ width: 120px; border-radius: 10px; }}
    h1 {{ color: #fff; margin: 0; }}
    .collapsible {{ background-color: #007BFF; color: white; cursor: pointer; padding: 10px; width: 100%; border: none; font-size: 16px; border-radius: 5px; margin-top: 10px; }}
    .collapsible:hover {{ background-color: #0056b3; }}
    .content {{ padding: 10px 18px; display: none; background-color: #ffffff; margin-top: 5px; border-radius: 5px; }}
    .section {{ border: 1px solid #ddd; border-radius: 4px; margin-bottom: 8px; padding: 5px; }}
    .item {{ padding: 8px; border-bottom: 1px solid #ccc; text-align: center; }}
    .footer-strip {{ margin-top: 40px; padding: 10px; text-align: center; background: linear-gradient(to right, #ff6a00, #ee0979); color: white; border-radius: 8px; }}
    p {{ text-align: center; font-size: 16px; margin: 10px; }}
    .datetime {{ text-align: center; font-size: 14px; color: #555; }}
  </style>
</head>
<body>
  <div class=\"loading-wrapper\">
    <div class=\"loading-text\">Welcome To Engineer's Babu</div>
    <div class=\"progress-bar\"><div class=\"progress-bar-fill\"></div></div>
    <div class=\"loading-text\">Your Content is preparing</div>
  </div>
  <div class=\"container\">
    <div class=\"header\">
      <img class=\"thumbnail\" src=\"{THUMBNAIL_URL}\" alt=\"Thumbnail\">
      <h1>{display_title}</h1>
    </div>
    <div class=\"datetime\">{formatted_datetime}</div>
    <p>♦️Use This Bot for JSON to HTML File Extraction : <a href=\"https://t.me/htmlextractorbot\" target=\"_blank\">@htmlextractorbot</a></p>
    {html_body}
    <div class=\"footer-strip\">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</div>
  </div>
  <script>
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener("click", function() {
        this.classList.toggle("active");
        const content = this.nextElementSibling;
        content.style.display = content.style.display === "block" ? "none" : "block";
      });
    }
  </script>
</body>
</html>
"""

# Message Handler
@bot.on_message(filters.document & filters.private)
async def handle_json(client: Client, message: Message):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.reply("❌ Please send a valid `.json` file.")
        return

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{sanitize_filename(doc.file_name)}"
    await message.download(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await message.reply(f"❌ Failed to parse JSON: {e}")
        return

    base_name = Path(doc.file_name).stem
    html = generate_html(data, base_name)
    output_path = f"downloads/{base_name}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    user = await client.get_users(message.from_user.id)
    users_col.update_one({"_id": user.id}, {"$set": {"name": user.first_name}}, upsert=True)

    await client.send_document("@kuvnypkyjk", document=file_path)
    await client.send_document("@kuvnypkyjk", document=output_path)

    await message.reply_document(
        document=output_path,
        caption=f"📖 𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 : {base_name}\n"
                f"🔗 𝐓𝐨𝐭𝐚𝐥 𝐋𝐢𝐧𝐤𝐬: {len(data)}\n"
                f"🎞️ 𝐕𝐢𝐝𝐞𝐨𝐬 : ? , 📚 𝐏𝐝𝐟𝐬 : ? , 💾 𝐎𝐭𝐡𝐞𝐫𝐬 : ?\n\n"
                f"👤User: {user.first_name or ''} {user.last_name or ''}\n🆔 ID: <code>{user.id}</code>\n"
                f"📅 {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d | ⏰ %H:%M:%S')}"
    )

    os.remove(file_path)
    os.remove(output_path)

# Admin Commands
@bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats(client: Client, message: Message):
    total = users_col.count_documents({})
    await message.reply_text(f"📊 Total users: {total}")

@bot.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
async def broadcast(client: Client, message: Message):
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
            await client.send_message(user_id, text)
            sent += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)

    await message.reply(f"✅ Broadcast done.\nTotal: {total}\nSent: {sent}\nFailed: {failed}")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pathlib import Path
from datetime import datetime

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Utilities ----------
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url):
    if "classplusapp" in url:
        url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={url}"
    if "/master.mpd" in url:
        vid = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid}"
    return url

def extract_name_url(text):
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data):
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

def generate_html(data, title):
    display_title = title.replace("_", " ")
    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    content_html = json_to_collapsible_html(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      background-color: #f8f9fa;
    }}
    .loader-container {{
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: #000;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: white;
      z-index: 9999;
    }}
    .container {{
      width: 1080px;
      margin: 20px auto;
      display: none;
    }}
    .header {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 20px;
      margin-bottom: 20px;
      justify-content: center;
      text-align: center;
      background: linear-gradient(135deg, #007BFF, #00C6FF, #7EE8FA, #EEC0C6);
      padding: 20px;
      border-radius: 15px;
    }}
    .thumbnail {{ width: 120px; border-radius: 10px; }}
    h1 {{ flex: 1 1 300px; text-align: center; margin: 0; color: #fff; }}
    .subheading {{ text-align: center; font-weight: bold; margin-bottom: 5px; }}
    .datetime {{ text-align: center; color: #888; font-size: 14px; }}
    .collapsible {{
      background-color: #007BFF;
      color: white;
      cursor: pointer;
      padding: 10px;
      width: 100%;
      border: none;
      text-align: center;
      outline: none;
      font-size: 16px;
      border-radius: 5px;
      margin-top: 10px;
    }}
    .active, .collapsible:hover {{ background-color: #0056b3; }}
    .content {{
      padding: 10px 18px;
      display: none;
      overflow: hidden;
      background-color: #ffffff;
      margin-top: 5px;
      border-radius: 5px;
    }}
    .section {{
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 8px;
      padding: 5px;
    }}
    .item {{ padding: 8px; border-bottom: 1px solid #ccc; text-align: center; }}
    a {{ text-decoration: none; color: #333; }}
    a:hover {{ color: #007BFF; }}
    .footer-strip {{
      margin-top: 40px;
      padding: 10px;
      text-align: center;
      background: linear-gradient(to right, #ff6a00, #ee0979);
      color: white;
      font-weight: bold;
      border-radius: 8px;
    }}
  </style>
</head>
<body>
  <div class="loader-container" id="loader">
    <h1>Welcome To Engineer's Babu</h1>
    <p>Your Content is Preparing...</p>
  </div>
  <div class="container" id="main-content">
    <div class="header">
      <img class="thumbnail" src="{THUMBNAIL_URL}" alt="Thumbnail">
      <h1>{display_title}</h1>
    </div>
    <div class="subheading">📥 Extracted By : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
    <div class="datetime" id="datetime">{timestamp}</div><br>
    <p>🔹Use This Bot for TXT to HTML File Extraction : <a href="https://t.me/htmldeveloperbot" target="_blank">@htmldeveloperbot</a></p>
    {content_html}
    <div class="footer-strip">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</div>
  </div>
  <script>
    window.addEventListener("load", () => {{
      document.getElementById("loader").style.display = "none";
      document.getElementById("main-content").style.display = "block";
    }});
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {{
      collapsibles[i].addEventListener("click", function() {{
        this.classList.toggle("active");
        const content = this.nextElementSibling;
        content.style.display = content.style.display === "block" ? "none" : "block";
      }});
    }}
  </script>
</body>
</html>"""

# ---------- Handler ----------
@bot.on_message(filters.document & filters.private)
async def handle_json(client, message: Message):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        return await message.reply("❌ Please send a `.json` file.")

    os.makedirs("downloads", exist_ok=True)
    path = f"downloads/{sanitize_filename(doc.file_name)}"
    await message.download(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return await message.reply(f"❌ Error reading JSON: {e}")

    base_name = Path(doc.file_name).stem
    html_code = generate_html(data, base_name)
    output_path = f"downloads/{base_name}.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_code)

    await message.reply_document(
        document=output_path,
        caption=f"✅ HTML generated for **{base_name}**"
    )

    os.remove(path)
    os.remove(output_path)

# ---------- Start Bot ----------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
