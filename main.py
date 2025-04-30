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
<div class="section depth-{depth}">
  <button class="collapsible">
    <span class="key">{key}</span>
    <span class="toggle-icon">+</span>
  </button>
  <div class="content">{inner}</div>
</div>
"""
        elif isinstance(obj, list):
            if all(isinstance(item, (str, int, float)) for item in obj):
                html += '<div class="simple-list">'
                for item in obj:
                    text = str(item)
                    if "http" in text:
                        label, url = text.rsplit(":", 1)
                        html += f'<div class="list-item"><a href="{url.strip()}" target="_blank">{label.strip()}</a></div>'
                    else:
                        html += f'<div class="list-item">{text}</div>'
                html += '</div>'
            else:
                for item in obj:
                    html += recurse(item, depth)
        else:
            text = str(obj)
            if "http" in text:
                label, url = text.rsplit(":", 1)
                html += f'<div class="item"><a href="{url.strip()}" target="_blank" class="link-item">{label.strip()}</a></div>\n'
            else:
                html += f"<div class='item'>{text}</div>\n"
        return html

    return recurse(data)

def generate_html(json_data, original_name):
    safe_title = sanitize_filename(original_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_body = json_to_collapsible_html(json_data)

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title} | JSON Explorer</title>
  <style>
    :root {{
        --primary: #4361ee;
        --secondary: #3a0ca3;
        --accent: #f72585;
        --light: #f8f9fa;
        --dark: #212529;
        --dark-bg: #1a1a1a;
        --darker-bg: #121212;
        --card-bg: #2d2d2d;
        --text-light: #e0e0e0;
        --text-lighter: #f5f5f5;
        --success: #4cc9f0;
        --warning: #f8961e;
        --danger: #ef233c;
        --gray: #adb5bd;
    }}
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
        line-height: 1.6;
        color: var(--text-light);
        background: var(--dark-bg);
        padding: 20px;
        min-height: 100vh;
    }}
    
    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: var(--card-bg);
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        overflow: hidden;
        padding-bottom: 20px;
    }}
    
    .header {{
        background: linear-gradient(to right, var(--darker-bg), var(--dark-bg));
        color: white;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 30px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .thumbnail {{
        width: 80px;
        height: 80px;
        border-radius: 10px;
        object-fit: cover;
        border: 3px solid var(--primary);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        flex-shrink: 0;
    }}
    
    .header-content {{
        flex: 1;
    }}
    
    .header h1 {{
        font-size: 1.8rem;
        margin-bottom: 5px;
        font-weight: 600;
        color: var(--text-lighter);
    }}
    
    .header p {{
        opacity: 0.8;
        font-size: 0.9rem;
        color: var(--text-light);
    }}
    
    .meta {{
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: var(--gray);
        padding: 0 20px;
        margin-bottom: 20px;
    }}
    
    .section {{
        margin: 5px 15px;
    }}
    
    .depth-0 {{
        margin: 10px 0;
    }}
    
    .collapsible {{
        background: linear-gradient(to right, var(--primary), var(--secondary));
        color: white;
        cursor: pointer;
        padding: 12px 15px;
        width: 100%;
        border: none;
        text-align: left;
        outline: none;
        font-size: 1rem;
        border-radius: 8px;
        margin-top: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    
    .collapsible:hover {{
        background: linear-gradient(to right, var(--secondary), var(--primary));
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }}
    
    .collapsible.active {{
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }}
    
    .collapsible .key {{
        font-weight: 500;
    }}
    
    .collapsible .toggle-icon {{
        font-weight: bold;
        transition: transform 0.3s ease;
    }}
    
    .collapsible.active .toggle-icon {{
        transform: rotate(45deg);
    }}
    
    .content {{
        padding: 0 10px;
        max-height: 0;
        overflow: hidden;
        background-color: rgba(0, 0, 0, 0.2);
        transition: max-height 0.3s ease-out, padding 0.3s ease;
        border-left: 3px solid var(--primary);
        margin-left: 10px;
        border-radius: 0 0 8px 8px;
    }}
    
    .content.expanded {{
        max-height: 5000px;
        padding: 10px;
        margin-bottom: 15px;
    }}
    
    .item {{
        padding: 10px 15px;
        margin: 5px 0;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        transition: all 0.2s ease;
        color: var(--text-light);
    }}
    
    .item:hover {{
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(3px);
    }}
    
    .simple-list {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 10px;
        padding: 10px 0;
    }}
    
    .list-item {{
        background: rgba(255, 255, 255, 0.05);
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        color: var(--text-light);
    }}
    
    .list-item:hover {{
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    .link-item {{
        color: var(--success);
        font-weight: 500;
        display: inline-block;
        padding: 2px 0;
        border-bottom: 1px dashed var(--success);
        transition: all 0.2s ease;
    }}
    
    .link-item:hover {{
        color: var(--accent);
        border-bottom-color: var(--accent);
        text-decoration: none;
    }}
    
    .footer {{
        text-align: center;
        margin-top: 30px;
        padding: 15px;
        font-size: 0.8rem;
        color: var(--gray);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    @media (max-width: 768px) {{
        .container {{
            border-radius: 0;
        }}
        
        .header {{
            flex-direction: column;
            text-align: center;
            padding: 20px 15px;
        }}
        
        .thumbnail {{
            margin-bottom: 15px;
        }}
        
        .simple-list {{
            grid-template-columns: 1fr;
        }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <img src="https://i.postimg.cc/4N69wBLt/hat-hacker.webp" alt="Thumbnail" class="thumbnail">
      <div class="header-content">
        <h1>{safe_title}</h1>
        <p>Interactive JSON Explorer</p>
      </div>
    </div>
    
    <div class="meta">
      <span>Generated: {timestamp}</span>
      <span>JSON to HTML Converter</span>
    </div>
    
    {html_body}
    
    <div class="footer">
      <p>Generated by JSON Explorer Bot • Click on items to expand/collapse</p>
    </div>
  </div>
  
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const collapsibles = document.getElementsByClassName("collapsible");
      
      for (let i = 0; i < collapsibles.length; i++) {{
        collapsibles[i].addEventListener("click", function() {{
          this.classList.toggle("active");
          const content = this.nextElementSibling;
          
          if (content.classList.contains("expanded")) {{
            content.classList.remove("expanded");
            setTimeout(() => content.style.maxHeight = "0", 10);
          }} else {{
            content.classList.add("expanded");
            content.style.maxHeight = content.scrollHeight + "px";
          }}
        }});
        
        // Open first level by default
        if (this.parentElement.classList.contains('depth-0')) {{
          collapsibles[i].click();
        }}
      }}
      
      // Smooth animation for max-height
      const contents = document.getElementsByClassName("content");
      for (let i = 0; i < contents.length; i++) {{
        contents[i].addEventListener('transitionend', function() {{
          if (this.classList.contains('expanded')) {{
            this.style.maxHeight = 'none';
          }}
        }});
      }}
    }});
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

    # Create downloads directory if not exists
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
        caption=f"📊 **{base_name}**\nHere's your interactive JSON explorer with professional styling!",
        parse_mode="markdown"
    )

    # Clean up
    os.remove(file_path)
    os.remove(output_file)

# ------------- Start Bot ----------------
if __name__ == "__main__":
    print("✨ Bot is running with enhanced professional design...")
    bot.run()
