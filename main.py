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
        color: var(--dark);
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        min-height: 100vh;
    }}
    
    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        padding-bottom: 20px;
    }}
    
    .header {{
        background: linear-gradient(to right, var(--primary), var(--secondary));
        color: white;
        padding: 30px 20px;
        text-align: center;
        position: relative;
        margin-bottom: 30px;
    }}
    
    .header h1 {{
        font-size: 2.2rem;
        margin-bottom: 10px;
        font-weight: 600;
    }}
    
    .header p {{
        opacity: 0.9;
        font-size: 0.9rem;
    }}
    
    .logo {{
        width: 60px;
        height: 60px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .logo svg {{
        width: 30px;
        height: 30px;
        fill: var(--primary);
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
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    .collapsible:hover {{
        background: linear-gradient(to right, var(--secondary), var(--primary));
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
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
        background-color: white;
        transition: max-height 0.3s ease-out, padding 0.3s ease;
        border-left: 3px solid var(--primary);
        margin-left: 10px;
    }}
    
    .content.expanded {{
        max-height: 5000px;
        padding: 10px;
        margin-bottom: 15px;
    }}
    
    .item {{
        padding: 10px 15px;
        margin: 5px 0;
        background: var(--light);
        border-radius: 6px;
        transition: all 0.2s ease;
    }}
    
    .item:hover {{
        background: #e9ecef;
        transform: translateX(3px);
    }}
    
    .simple-list {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 10px;
        padding: 10px 0;
    }}
    
    .list-item {{
        background: #f8f9fa;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }}
    
    .list-item:hover {{
        background: #e9ecef;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}
    
    .link-item {{
        color: var(--primary);
        font-weight: 500;
        display: inline-block;
        padding: 2px 0;
        border-bottom: 1px dashed var(--primary);
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
        border-top: 1px solid #eee;
    }}
    
    @media (max-width: 768px) {{
        .container {{
            border-radius: 0;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
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
      <div class="logo">
        <svg viewBox="0 0 24 24">
          <path d="M5,3H19A2,2 0 0,1 21,5V19A2,2 0 0,1 19,21H5A2,2 0 0,1 3,19V5A2,2 0 0,1 5,3M7,5A2,2 0 0,0 5,7A2,2 0 0,0 7,9A2,2 0 0,0 9,7A2,2 0 0,0 7,5M17,15A2,2 0 0,0 15,17A2,2 0 0,0 17,19A2,2 0 0,0 19,17A2,2 0 0,0 17,15M17,5A2,2 0 0,0 15,7A2,2 0 0,0 17,9A2,2 0 0,0 19,7A2,2 0 0,0 17,5M7,15A2,2 0 0,0 5,17A2,2 0 0,0 7,19A2,2 0 0,0 9,17A2,2 0 0,0 7,15M16,10L18,12L16,14L14,12L16,10M8,10L10,12L8,14L6,12L8,10Z" />
        </svg>
      </div>
      <h1>{safe_title}</h1>
      <p>Interactive JSON Explorer</p>
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
