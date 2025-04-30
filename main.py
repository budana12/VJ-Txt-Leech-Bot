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

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ----------- HTML Generator -------------
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

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
<div class=\"section depth-{depth}\">
  <button class=\"collapsible\">
    <span class=\"key\">{key}</span>
    <span class=\"toggle-icon\">+</span>
  </button>
  <div class=\"content\">{inner}</div>
</div>
"""
        elif isinstance(obj, list):
            if all(isinstance(item, (str, int, float)) for item in obj):
                html += '<div class="simple-list">'
                for item in obj:
                    text = str(item)
                    if "http" in text:
                        if ':' in text:
                            label, url = text.rsplit(":", 1)
                            html += f'<div class="list-item"><a href="{url.strip()}" target="_blank">{label.strip()}</a></div>'
                        else:
                            html += f'<div class="list-item"><a href="{text.strip()}" target="_blank">{text.strip()}</a></div>'
                    else:
                        html += f'<div class="list-item">{text}</div>'
                html += '</div>'
            else:
                for item in obj:
                    html += recurse(item, depth)
        else:
            text = str(obj)
            if "http" in text:
                if ':' in text:
                    label, url = text.rsplit(":", 1)
                    html += f'<div class="item"><a href="{url.strip()}" target="_blank" class="link-item">{label.strip()}</a></div>\n'
                else:
                    html += f'<div class="item"><a href="{text.strip()}" target="_blank" class="link-item">{text.strip()}</a></div>\n'
            else:
                html += f"<div class='item'>{text}</div>\n"
        return html

    return recurse(data)

def generate_html(json_data, original_name):
    safe_title = sanitize_filename(original_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_body = json_to_collapsible_html(json_data)

    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    return template.replace("{{TITLE}}", safe_title).replace("{{TIMESTAMP}}", timestamp).replace("{{BODY}}", html_body)

# ----------- Handlers ------------------
@bot.on_message(filters.document & filters.private)
async def handle_json_file(client: Client, message: Message):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.reply("Please send a valid `.json` file.")
        return

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{sanitize_filename(doc.file_name)}"
    await message.download(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await message.reply(f"Failed to parse JSON: {e}")
        os.remove(file_path)
        return

    base_name = Path(doc.file_name).stem
    html = generate_html(data, base_name)
    output_file = f"downloads/{sanitize_filename(base_name)}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    await message.reply_document(
        document=output_file,
        caption=f"\ud83d\udcca **{base_name}**\nHere's your interactive JSON explorer with professional styling!",
        parse_mode="Markdown"
    )

    os.remove(file_path)
    os.remove(output_file)

# ------------- Start Bot ----------------
if __name__ == "__main__":
    print("\u2728 Bot is running with enhanced professional design...")
    bot.run()
