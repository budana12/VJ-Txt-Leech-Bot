import os
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pathlib import Path
from datetime import datetime

# ------------- Bot Config ----------------
API_ID = 123456  # Replace with your API ID
API_HASH = "your_api_hash"  # Replace with your API HASH
BOT_TOKEN = "your_bot_token"  # Replace with your BOT token

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
<div class="section">
  <button class="collapsible">{key}</button>
  <div class="content">{inner}</div>
</div>
"""
        elif isinstance(obj, list):
            for item in obj:
                html += recurse(item, depth)
        else:
            text = str(obj)
            if "http" in text:
                label, url = text.rsplit(":", 1)
                html += f'<div class="item"><a href="{url.strip()}" target="_blank">{label.strip()}</a></div>\n'
            else:
                html += f"<div class='item'>{text}</div>\n"
        return html

    return recurse(data)

def generate_html(json_data, original_name):
    safe_title = sanitize_filename(original_name)
    html_body = json_to_collapsible_html(json_data)

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{safe_title}</title>
  <style>
    body {{
        font-family: Arial, sans-serif;
        margin: 20px;
        background-color: #f8f9fa;
    }}
    .header {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .thumbnail {{
        width: 120px;
        border-radius: 10px;
    }}
    .collapsible {{
        background-color: #007BFF;
        color: white;
        cursor: pointer;
        padding: 10px;
        width: 100%;
        border: none;
        text-align: left;
        outline: none;
        font-size: 16px;
        border-radius: 5px;
        margin-top: 10px;
    }}
    .active, .collapsible:hover {{
        background-color: #0056b3;
    }}
    .content {{
        padding: 0 18px;
        display: none;
        overflow: hidden;
        background-color: #f1f1f1;
        margin-top: 5px;
        border-radius: 5px;
    }}
    .item {{
        padding: 8px;
        border-bottom: 1px solid #ccc;
    }}
    a {{
        text-decoration: none;
        color: #333;
    }}
    a:hover {{
        color: #007BFF;
    }}
  </style>
</head>
<body>
  <div class="header">
    <img class="thumbnail" src="https://via.placeholder.com/150x150.png?text=Thumbnail" alt="Thumbnail">
    <h1>{safe_title}</h1>
  </div>
  {html_body}
  <script>
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {{
      collapsibles[i].addEventListener("click", function() {{
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
</html>
"""
    return html_template

# ----------- Handlers ------------------
@bot.on_message(filters.document & filters.private)
async def handle_json_file(client: Client, message: Message):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.reply("Please send a valid `.json` file.")
        return

    file_path = f"downloads/{sanitize_filename(doc.file_name)}"
    await message.download(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await message.reply(f"Failed to parse JSON: {e}")
        return

    base_name = Path(doc.file_name).stem
    html = generate_html(data, base_name)
    output_file = f"downloads/{sanitize_filename(base_name)}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    await message.reply_document(
        document=output_file,
        caption=f"Here is your structured HTML for **{base_name}**",
    )

    os.remove(file_path)
    os.remove(output_file)

# ------------- Start Bot ----------------
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
