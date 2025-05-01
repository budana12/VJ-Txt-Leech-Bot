import os
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import Message

# --------- Bot Config ----------
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAF_XoWPfbmRUtMSg7B1xDBtUdd8JpZXgP4"
THUMBNAIL_URL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
ADMIN_ID = 1147534909  # Replace with your Telegram user ID

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                date_joined TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

init_db()

bot = Client("json_to_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Utilities ----------
def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9 .\-]', '_', name)

def modify_url(url: str) -> str:
    if "classplusapp" in url:
        url = url.split("://")[-1] if "://" in url else url
        return f"https://api.extractor.workers.dev/player?url={url}"
    if "/master.mpd" in url:
        vid = url.split("/")[-2]
        return f"https://player.muftukmall.site/?id={vid}"
    return url

def extract_name_url(text: str) -> tuple:
    match = re.match(r"^(.*?)(https?://\S+)$", text.strip())
    if match:
        name, url = match.groups()
        return name.strip(" :"), modify_url(url.strip())
    return text.strip(), None

def json_to_collapsible_html(data) -> str:
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

def generate_html(data, title: str) -> str:
    display_title = title.replace("_", " ")
    content_html = json_to_collapsible_html(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    body {{
      font-family: 'Poppins', sans-serif;
      margin: 0;
      background-color: #f8f9fa;
    }}
    
    .loading-wrapper {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: white;
      z-index: 9999;
    }}
    
    .loading-text {{
      font-size: 2rem;
      font-weight: 600;
      margin-bottom: 2rem;
      background: linear-gradient(90deg, #00dbde, #fc00ff);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      text-align: center;
    }}
    
    .progress-container {{
      width: 80%;
      max-width: 400px;
      text-align: center;
    }}
    
    .progress-text {{
      margin-top: 1rem;
      font-size: 1rem;
      color: #a1a1a1;
    }}
    
    .progress-bar {{
      width: 100%;
      height: 10px;
      background-color: #2c2c54;
      border-radius: 10px;
      overflow: hidden;
    }}
    
    .progress-bar-fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #00dbde, #fc00ff);
      border-radius: 10px;
      animation: progress 2s ease-in-out infinite;
    }}
    
    @keyframes progress {{
      0% {{ width: 0%; }}
      50% {{ width: 100%; }}
      100% {{ width: 0%; left: 100%; }}
    }}
    
    .container {{
      width: 850px;
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
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }}
    
    .thumbnail {{
      width: 120px;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    
    h1 {{
      flex: 1 1 300px;
      text-align: center;
      margin: 0;
      color: #fff;
      font-weight: 700;
      text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }}
    
    .info-container {{
      text-align: center;
      margin: 20px 0;
      padding: 15px;
      background: #ffffff;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }}
    
    .datetime {{
      font-size: 14px;
      color: #555;
      margin: 10px 0;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 5px;
    }}
    
    .bot-info {{
      text-align: center;
      padding: 15px;
      margin: 20px auto;
      background: linear-gradient(to right, #f5f7fa, #c3cfe2);
      border-radius: 10px;
      max-width: 80%;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    .collapsible {{
      background: linear-gradient(135deg, #6e8efb, #a777e3);
      color: white;
      cursor: pointer;
      padding: 12px;
      width: 100%;
      border: none;
      text-align: center;
      outline: none;
      font-size: 16px;
      border-radius: 8px;
      margin-top: 10px;
      font-weight: 600;
      transition: all 0.3s ease;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    .active, .collapsible:hover {{
      background: linear-gradient(135deg, #5a7bf9, #9664d4);
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    
    .content {{
      padding: 10px 18px;
      display: none;
      overflow: hidden;
      background-color: #ffffff;
      margin-top: 5px;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}
    
    .section {{
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 5px;
      background: #f9f9f9;
    }}
    
    .item {{
      padding: 10px;
      border-bottom: 1px solid #eee;
      text-align: center;
      transition: background 0.2s;
    }}
    
    .item:hover {{
      background: #f0f0f0;
    }}
    
    a {{
      text-decoration: none;
      color: #4a6bff;
      font-weight: 500;
    }}
    
    a:hover {{
      color: #2a4bdf;
      text-decoration: underline;
    }}
    
    .footer-strip {{
      margin-top: 40px;
      padding: 15px;
      text-align: center;
      background: linear-gradient(to right, #ff6a00, #ee0979);
      color: white;
      font-weight: 600;
      border-radius: 8px;
      font-size: 1.1rem;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .stats {{
      display: flex;
      justify-content: space-around;
      margin: 20px 0;
      flex-wrap: wrap;
      gap: 10px;
    }}
    
    .stat-box {{
      background: white;
      padding: 15px;
      border-radius: 10px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
      flex: 1;
      min-width: 120px;
      text-align: center;
    }}
    
    .stat-value {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #6e8efb;
      margin: 5px 0;
    }}
    
    .stat-label {{
      font-size: 0.9rem;
      color: #666;
    }}
  </style>
</head>
<body>
  <div class="loading-wrapper" id="loader">
    <div class="loading-text">Welcome To Engineer's Babu</div>
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-bar-fill"></div>
      </div>
      <div class="progress-text">Your Content is Preparing...</div>
    </div>
  </div>
  
  <div class="container" id="main-content">
    <div class="header">
      <img class="thumbnail" src="{THUMBNAIL_URL}" alt="Thumbnail">
      <h1>{display_title}</h1>
    </div>
    
    <div class="info-container">
      <div class="datetime">
        📅 Date: {datetime.now().strftime('%d-%m-%Y')} | 🕒 Time: {datetime.now().strftime('%I:%M %p')}
      </div>
      <div class="subheading">📥 Extracted By: <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div>
    </div>
    
    <div class="stats">
      <div class="stat-box">
        <div class="stat-value">{len(data)}</div>
        <div class="stat-label">Total Items</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{sum(1 for item in json.dumps(data) if '"http' in json.dumps(data))}</div>
        <div class="stat-label">Links Found</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{datetime.now().strftime('%H:%M')}</div>
        <div class="stat-label">Generated At</div>
      </div>
    </div>
    
    <div class="bot-info">
      ✨ Use This Bot for JSON to HTML File Extraction: <a href="https://t.me/htmlextractorbot" target="_blank">@htmlextractorbot</a>
      <br><br>
      🔔 Broadcast Channel: <a href="https://t.me/engineersbabu" target="_blank">@EngineersBabu</a>
    </div>
    
    {content_html}
    
    <div class="footer-strip">
      𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™ © {datetime.now().strftime('%Y')}
    </div>
  </div>
  
  <script>
    window.addEventListener("load", () => {{
      // Simulate loading completion
      setTimeout(() => {{
        document.getElementById("loader").style.display = "none";
        document.getElementById("main-content").style.display = "block";
        
        // Update datetime every minute
        setInterval(updateDateTime, 60000);
        updateDateTime();
      }}, 1500);
    }});
    
    function updateDateTime() {{
      const now = new Date();
      const dateStr = now.toLocaleDateString('en-IN', {{ day: '2-digit', month: '2-digit', year: 'numeric' }});
      const timeStr = now.toLocaleTimeString('en-IN', {{ hour: '2-digit', minute: '2-digit' }});
      document.querySelector('.datetime').innerHTML = `📅 Date: ${{dateStr}} | 🕒 Time: ${{timeStr}}`;
    }}
    
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

# ---------- Database Functions ----------
def add_user(user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]):
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, date_joined)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"Error adding user: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def get_total_users() -> int:
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        return count or 0
    except Exception as e:
        print(f"Error getting user count: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def get_all_users() -> List[int]:
    try:
        conn = sqlite3.connect('bot_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        return users or []
    except Exception as e:
        print(f"Error getting user list: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# ---------- Handlers ----------
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    try:
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        await message.reply(
            "👋 Hi! Send me a JSON file and I'll convert it to a beautiful HTML file with collapsible sections.\n\n"
            "📌 Just upload any JSON file and I'll handle the rest!"
        )
    except Exception as e:
        print(f"Error in start command: {e}")

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    try:
        total_users = get_total_users()
        await message.reply(
            f"📊 Bot Statistics:\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📅 Last Updated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
        )
    except Exception as e:
        print(f"Error in stats command: {e}")
        await message.reply("❌ Error fetching statistics. Please try again later.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    try:
        if message.from_user.id != ADMIN_ID:
            await message.reply("❌ You are not authorized to use this command.")
            return
        
        if not message.reply_to_message:
            await message.reply("⚠️ Please reply to a message you want to broadcast.")
            return
        
        users = get_all_users()
        if not users:
            await message.reply("❌ No users found in database.")
            return
        
        total = len(users)
        success = 0
        failed = 0
        
        progress = await message.reply(f"📢 Broadcasting to {total} users...\n\n✅ Success: 0\n❌ Failed: 0")
        
        for user_id in users:
            try:
                await message.reply_to_message.copy(user_id)
                success += 1
            except Exception as e:
                failed += 1
                print(f"Failed to send to {user_id}: {e}")
            
            if (success + failed) % 10 == 0 or (success + failed) == total:
                try:
                    await progress.edit_text(
                        f"📢 Broadcasting to {total} users...\n\n"
                        f"✅ Success: {success}\n"
                        f"❌ Failed: {failed}\n"
                        f"📊 Progress: {success + failed}/{total} ({((success + failed)/total)*100:.1f}%)"
                    )
                except Exception as e:
                    print(f"Error updating progress: {e}")
        
        await progress.edit_text(
            f"📢 Broadcast completed!\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Total: {total} users"
        )
    except Exception as e:
        print(f"Error in broadcast command: {e}")
        await message.reply("❌ Error during broadcast. Please check logs.")

@bot.on_message(filters.document & filters.private)
async def handle_json(client: Client, message: Message):
    try:
        # Add user to database
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        
        doc = message.document
        if not doc.file_name.endswith(".json"):
            return

        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/{sanitize_filename(doc.file_name)}"
        
        # Download file silently
        await message.download(path)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            os.remove(path)
            return
        
        base_name = Path(doc.file_name).stem
        html_code = generate_html(data, base_name)
        output_path = f"downloads/{base_name}.html"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_code)

        # Send the HTML file silently
        await client.send_document(
            chat_id=message.chat.id,
            document=output_path,
            caption=f"✅ HTML generated for **{base_name}**",
            thumb=THUMBNAIL_URL
        )
        
        # Clean up files
        os.remove(path)
        os.remove(output_path)
        
    except Exception as e:
        print(f"Error handling JSON: {e}")
        # No error message sent to user as requested
        if 'path' in locals() and os.path.exists(path):
            os.remove(path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

# ---------- Start Bot ----------
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    try:
        bot.run()
    except Exception as e:
        print(f"Bot crashed: {e}")
    finally:
        print("Bot stopped")
