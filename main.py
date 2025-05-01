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
