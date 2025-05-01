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
MONGO_URL = "mongodb://localhost:27017"
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
            link_type = 'other'
            if url and 'video' in url:
                link_type = 'video'
            elif url and 'document' in url:
                link_type = 'doc'

            if url:
                html += f'<div class="item" data-type="{link_type}"><a href="{url}" target="_blank">{name}</a></div>\n'
            else:
                html += f"<div class='item' data-type='{link_type}'>{name}</div>\n"
        return html
    return recurse(data)

def generate_html(data, title):
    display_title = title.replace("_", " ")
    content_html = json_to_collapsible_html(data)

    # Adding clickable filters to show specific link types
    filter_buttons = """
    <div class="filter-buttons">
        <button class="filter" onclick="filterLinks('all')">Show All</button>
        <button class="filter" onclick="filterLinks('video')">Videos</button>
        <button class="filter" onclick="filterLinks('doc')">Documents</button>
        <button class="filter" onclick="filterLinks('other')">Other Links</button>
    </div>
    """

    # Adding script to filter links based on type
    script = """
    <script>
      function filterLinks(type) {
        const allItems = document.querySelectorAll('.item');
        allItems.forEach(item => {
          const isVideo = item.dataset.type === 'video';
          const isDoc = item.dataset.type === 'doc';
          const isOther = item.dataset.type === 'other';

          if (type === 'all') {
            item.style.display = 'block';
          } else if (type === 'video' && isVideo) {
            item.style.display = 'block';
          } else if (type === 'doc' && isDoc) {
            item.style.display = 'block';
          } else if (type === 'other' && isOther) {
            item.style.display = 'block';
          } else {
            item.style.display = 'none';
          }
        });
      }
    </script>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; }}
    .filter-buttons {{ text-align: center; margin: 20px 0; }}
    .filter {{ background-color: #007BFF; color: white; cursor: pointer; padding: 10px 20px; margin: 0 5px; border-radius: 5px; border: none; font-size: 16px; }}
    .filter:hover {{ background-color: #0056b3; }}
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
  <div class="loader-container" id="loader">
    <div class="loading-text">Welcome To Engineer's Babu</div>
    <div class="progress-bar"><div class="progress-bar-fill"></div></div>
    <div style="margin-top:10px;">🛠 Your Content is preparing...</div>
  </div>
  <div class="container" id="main-content">
    <div class="header">
      <img class="thumbnail" src="{THUMBNAIL_URL}" alt="Thumbnail">
      <h1>{display_title}</h1>
    </div>
    <div class="subheading">📅 Extracted By : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div>
    <div class="datetime" id="datetime"></div>
    <p class="bot-link">♦️Use This Bot for JSON to HTML File Extraction : <a href="https://t.me/htmlextractorbot" target="_blank">@htmlextractorbot</a></p>
    {filter_buttons}
    {content_html}
    {script}
    <div class="footer-strip">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</div>
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
    db.users.update_one({"_id": user_id}, {"$set": {"last_activity": datetime.now()}}, upsert=True)
    if message.document.mime_type == 'application/json':
        file = await message.download()
        with open(file, "r") as f:
            json_data = json.load(f)
        title = sanitize_filename(message.document.file_name)
        html_content = generate_html(json_data, title)
        file_name = f"{title}.html"
        html_path = f"/tmp/{file_name}"
        with open(html_path, "w") as f:
            f.write(html_content)
        
        # Send HTML file back to the user
        await message.reply_document(html_path, caption=f"📄 **HTML Generated:** `{file_name}`")
        os.remove(file)
        os.remove(html_path)

# --------- Start Bot ----------
bot.run()
