import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pathlib import Path
from datetime import datetime

# ------------- Bot Config ----------------
API_ID = 21705536  # Replace with your API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"  # Replace with your API HASH
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"  # Replace with your BOT token
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"  # Thumbnail URL

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ========== UTILS ===============
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
    display_title = original_name.replace("_", " ")  # Keep spaces
    formatted_datetime = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    html_body = json_to_collapsible_html(json_data)

    html_template = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>{display_title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 20px;
      background-color: #f8f9fa;
      display: flex;
      justify-content: center;
    }}
    .container {{ width: 640px; }}
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
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <img class=\"thumbnail\" src=\"{THUMBNAIL_URL}\" alt=\"Thumbnail\">
      <h1>{display_title}</h1>
    </div>
    <div class="subheading">📥 Extracted By : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
    <div class="datetime" id="datetime">{formatted_datetime}</div><br>
    <p>🔹Use This Bot for TXT to HTML File Extraction : <a href="https://t.me/htmldeveloperbot" target="_blank">@htmldeveloperbot</a></p>
    {html_body}
  </div>
  <script>
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {
      collapsibles[i].addEventListener("click", function() {
        this.classList.toggle("active");
        const content = this.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
    }
  </script>
</body>
</html>
"""
    return html_template

# ========== HANDLER ================
@bot.on_message(filters.document & filters.private)
async def handle_json_file(client: Client, message: Message):
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
    output_file = f"downloads/{base_name}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    await message.reply_document(
        document=output_file,
        caption=f"✅ Structured HTML created for **{base_name}**",
    )

    os.remove(file_path)
    os.remove(output_file)

# ========== START BOT ===============
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
