import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
MONGO_URL = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_IDS = [6203960005]  # Add your Telegram user ID here

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URL)
db = mongo.json_to_html

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

def generate_html(data, title):
    display_title = title.replace("_", " ")
    content_html = json_to_collapsible_html(data)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>{display_title}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; }}
    .loader-container {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #0a0a0a; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; z-index: 9999; }}
    .loading-text {{ font-size: 28px; font-weight: bold; margin-bottom: 20px; }}
    .progress-bar {{ width: 300px; height: 20px; background: #444; border-radius: 10px; overflow: hidden; }}
    .progress-bar-fill {{ width: 0%; height: 100%; background: linear-gradient(90deg, #ff6a00, #f20089); animation: loading 3s infinite; }}
    @keyframes loading {{
      0% {{ width: 0%; }}
      50% {{ width: 100%; }}
      100% {{ width: 0%; }}
    }}
    .container {{ max-width: 850px; margin: 20px auto; display: none; }}
    .header {{ display: flex; flex-wrap: wrap; justify-content: center; background: linear-gradient(135deg, #007BFF, #00C6FF); padding: 20px; border-radius: 15px; text-align: center; }}
    .thumbnail {{ width: 100px; border-radius: 10px; }}
    h1 {{ margin: 0; color: #fff; flex: 1 1 100%; }}
    .subheading, .datetime, .bot-link {{ text-align: center; font-weight: bold; margin: 10px 0; }}
    .datetime {{ color: #666; }}
    .collapsible {{ background-color: #007BFF; color: white; cursor: pointer; padding: 10px; width: 100%; border: none; text-align: center; outline: none; font-size: 16px; border-radius: 5px; margin-top: 10px; }}
    .active, .collapsible:hover {{ background-color: #0056b3; }}
    .content {{ padding: 10px 18px; display: none; background-color: #ffffff; margin-top: 5px; border-radius: 5px; }}
    .section {{ border: 1px solid #ddd; border-radius: 4px; margin-bottom: 8px; padding: 5px; }}
    .item {{ padding: 8px; border-bottom: 1px solid #ccc; text-align: center; }}
    a {{ text-decoration: none; color: #333; }}
    a:hover {{ color: #007BFF; }}
    .footer-strip {{ margin-top: 40px; padding: 10px; text-align: center; background: linear-gradient(to right, #ff6a00, #ee0979); color: white; font-weight: bold; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class=\"loader-container\" id=\"loader\">
    <div class=\"loading-text\">Welcome To Engineer's Babu</div>
    <div class=\"progress-bar\"><div class=\"progress-bar-fill\"></div></div>
    <div style=\"margin-top:10px;\">🛠 Your Content is preparing...</div>
  </div>
  <div class=\"container\" id=\"main-content\">
    <div class=\"header\">
      <img class=\"thumbnail\" src=\"{THUMBNAIL_URL}\" alt=\"Thumbnail\">
      <h1>{display_title}</h1>
    </div>
    <div class=\"subheading\">📅 Extracted By : <a href=\"https://t.me/Engineersbabuhelpbot\" target=\"_blank\">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div>
    <div class=\"datetime\" id=\"datetime\"></div>
    <p class=\"bot-link\">♦️Use This Bot for JSON to HTML File Extraction : <a href=\"https://t.me/htmlextractorbot\" target=\"_blank\">@htmlextractorbot</a></p>
    {content_html}
    <div class=\"footer-strip\">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</div>
  </div>
  <script>
    const updateDateTime = () => {
      const dt = new Date();
      document.getElementById("datetime").innerText = `📆 ${dt.toLocaleDateString()} ⏰ ${dt.toLocaleTimeString()}`;
    };
    window.addEventListener("load", () => {
      document.getElementById("loader").style.display = "none";
      document.getElementById("main-content").style.display = "block";
      updateDateTime();
      setInterval(updateDateTime, 1000);
    });
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {
      collapsibles[i].addEventListener("click", function () {
        this.classList.toggle("active");
        const content = this.nextElementSibling;
        content.style.display = content.style.display === "block" ? "none" : "block";
      });
    }
  </script>
</body>
</html>"""

# ---------- Handlers ----------
@bot.on_message(filters.document & filters.private)
async def handle_json(client, message: Message):
    user_id = message.from_user.id
    db.users.update_one({"_id": user_id}, {"$set": {"name": message.from_user.first_name}}, upsert=True)

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

@bot.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_handler(client, message):
    count = db.users.count_documents({})
    await message.reply(f"📊 Total Users: **{count}**")

@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_handler(client, message):
    if not message.reply_to_message:
        return await message.reply("❌ Reply to a message to broadcast.")

    users = db.users.find()
    success, failed = 0, 0
    for user in users:
        try:
            await message.reply_to_message.copy(user["_id"])
            success += 1
        except:
            failed += 1
            await message.reply(f"✅ Broadcast Done\nSuccess: {success}\nFailed: {failed}")

# ---------- Start Bot ----------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
