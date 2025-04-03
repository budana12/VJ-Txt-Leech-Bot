

import os
import hashlib
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import secrets
import html
import requests

# ===== CONFIGURATION =====
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8193765546:AAEs_Ul-zoQKAto5-I8vYJpGSZgDEa-POeU"
SECRET_KEY = "khvhgfnkjfdsbjuhb"

# Default thumbnail (using a reliable placeholder)
DEFAULT_THUMBNAIL_URL = "https://via.placeholder.com/150/007bff/ffffff?text=HTML"
THUMBNAIL_PATH = "thumbnail.jpg"

# ===== BOT SETUP =====
app = Client("secure_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== UTILITY FUNCTIONS =====
def generate_user_token(user_id):
    """Generate a secure token based on user ID and secret key"""
    return hashlib.sha256(f"{user_id}{SECRET_KEY}".encode()).hexdigest()

def generate_access_code():
    """Generate a random 8-digit access code"""
    return ''.join(secrets.choice('0123456789') for _ in range(8))

def download_default_thumbnail():
    """Download the default thumbnail if it doesn't exist"""
    if not os.path.exists(THUMBNAIL_PATH):
        try:
            response = requests.get(DEFAULT_THUMBNAIL_URL, stream=True)
            response.raise_for_status()
            with open(THUMBNAIL_PATH, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        except Exception as e:
            print(f"Couldn't download thumbnail: {e}")
            return None
    return THUMBNAIL_PATH

def extract_names_and_urls(file_content):
    """Extract name:URL pairs from text content"""
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
    """Categorize URLs into videos, PDFs, and others"""
    videos, pdfs, others = [], [], []
    
    for name, url in urls:
        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpd']):
            videos.append((name, url))
        elif 'youtube.com' in url or 'youtu.be' in url:
            videos.append((name, url))
        elif 'classplusapp.com' in url or 'testbook.com' in url:
            videos.append((name, f"https://dragoapi.vercel.app/video/{url}"))
        elif '.pdf' in url.lower():
            pdfs.append((name, url))
        elif '.zip' in url.lower():
            videos.append((name, f"https://video.pablocoder.eu.org/appx-zip?url={url}"))
        else:
            others.append((name, url))
    
    return videos, pdfs, others

def generate_html(file_name, videos, pdfs, others, user_id, user_token, access_code):
    """Generate the HTML file with authentication"""
    base_name = os.path.splitext(file_name)[0]
    escaped_base_name = html.escape(base_name)
    
    # Generate content links
    video_links = "".join(
        f'<div class="item"><a href="#" onclick="playVideo(\'{html.escape(url)}\')">{html.escape(name)}</a></div>'
        for name, url in videos
    )
    pdf_links = "".join(
        f'<div class="item"><a href="{html.escape(url)}" target="_blank">{html.escape(name)}</a></div>'
        for name, url in pdfs
    )
    other_links = "".join(
        f'<div class="item"><a href="{html.escape(url)}" target="_blank">{html.escape(name)}</a></div>'
        for name, url in others
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_base_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f7fa;
        }}
        .auth-container {{
            max-width: 400px;
            margin: 50px auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .auth-form input {{
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        .auth-form button {{
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .content {{
            display: none;
            padding: 20px;
        }}
        .tab {{
            padding: 10px 15px;
            margin: 5px;
            background: #007bff;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            display: inline-block;
        }}
        .tab-content {{
            display: none;
            margin-top: 20px;
        }}
        .item {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
        }}
        .item a {{
            text-decoration: none;
            color: #007bff;
        }}
        .error {{
            color: red;
            margin-top: 10px;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="auth-container" class="auth-container">
        <h2 style="text-align: center;">Secure Content Access</h2>
        <div class="auth-form">
            <input type="text" id="userIdInput" placeholder="Your User ID">
            <input type="text" id="accessCodeInput" placeholder="Access Code">
            <button onclick="verifyAccess()">Verify</button>
            <div id="errorMsg" class="error">Invalid credentials</div>
        </div>
    </div>

    <div id="content" class="content">
        <h1 style="text-align: center;">{escaped_base_name}</h1>
        <div style="text-align: center;">
            <div class="tab" onclick="showTab('videos')">Videos ({len(videos)})</div>
            <div class="tab" onclick="showTab('pdfs')">PDFs ({len(pdfs)})</div>
            <div class="tab" onclick="showTab('others')">Others ({len(others)})</div>
        </div>
        
        <div id="videos" class="tab-content">
            <h2>Video Lectures</h2>
            {video_links}
        </div>
        
        <div id="pdfs" class="tab-content">
            <h2>PDF Documents</h2>
            {pdf_links}
        </div>
        
        <div id="others" class="tab-content">
            <h2>Other Resources</h2>
            {other_links}
        </div>
    </div>

    <script>
        // Required credentials
        const REQUIRED_USER_ID = "{user_id}";
        const REQUIRED_TOKEN = "{user_token}";
        const ACCESS_CODE = "{access_code}";
        
        // Verify access
        function verifyAccess() {{
            const userId = document.getElementById('userIdInput').value;
            const accessCode = document.getElementById('accessCodeInput').value;
            
            if (userId === REQUIRED_USER_ID && accessCode === ACCESS_CODE) {{
                // Store verification in sessionStorage (temporary)
                sessionStorage.setItem('verified', 'true');
                sessionStorage.setItem('userId', userId);
                
                // Show content
                document.getElementById('auth-container').style.display = 'none';
                document.getElementById('content').style.display = 'block';
                showTab('videos');
            }} else {{
                document.getElementById('errorMsg').style.display = 'block';
            }}
        }}
        
        // Show tab
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(el => {{
                el.style.display = 'none';
            }});
            document.getElementById(tabName).style.display = 'block';
        }}
        
        // Play video
        function playVideo(url) {{
            if (url.includes('youtube.com') || url.includes('youtu.be')) {{
                window.open(url, '_blank');
            }} else {{
                alert('Video playback would start for: ' + url);
            }}
        }}
        
        // Check if already verified
        if (sessionStorage.getItem('verified') === 'true' && 
            sessionStorage.getItem('userId') === REQUIRED_USER_ID) {{
            document.getElementById('auth-container').style.display = 'none';
            document.getElementById('content').style.display = 'block';
            showTab('videos');
        }}
    </script>
</body>
</html>"""
    return html_content

# Download default thumbnail at startup
download_default_thumbnail()

# ===== TELEGRAM HANDLERS =====
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{message.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

@app.on_message(filters.document)
async def document_handler(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("❌ Please upload a .txt file with name:URL pairs.")
        return
    
    user = message.from_user
    user_id = user.id
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    # Generate secure tokens
    user_token = generate_user_token(user_id)
    access_code = generate_access_code()
    
    # Download and process file
    file_path = await message.download()
    html_path = ""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
        
        urls = extract_names_and_urls(content)
        videos, pdfs, others = categorize_urls(urls)
        
        # Generate HTML
        html_content = generate_html(
            message.document.file_name,
            videos, pdfs, others,
            user_id, user_token, access_code
        )
        
        html_path = file_path.replace(".txt", ".html")
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        # Get thumbnail (use default if available)
        thumb = THUMBNAIL_PATH if os.path.exists(THUMBNAIL_PATH) else None
        
        # Send to user with strict instructions
        await message.reply_document(
            document=html_path,
            file_name=f"secure_{os.path.splitext(message.document.file_name)[0]}.html",
            caption=(
                f"🔐 Secure HTML File\n\n"
                f"👤 User ID: <code>{user_id}</code>\n"
                f"🔑 Access Code: <code>{access_code}</code>\n\n"
                "⚠️ Important:\n"
                "1. Do NOT share this file with anyone\n"
                "2. The access code will be required to view content\n"
                "3. The file is tied to your User ID only\n\n"
                "You will need both your User ID and Access Code to view the content."
            ),
            thumb=thumb
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error processing file: {str(e)}")
    finally:
        # Cleanup temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        if html_path and os.path.exists(html_path):
            os.remove(html_path)

@app.on_callback_query(filters.regex("^help$"))
async def help_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "📚 Help Guide\n\n"
        "1. Prepare a .txt file with content like:\n"
        "<code>Lecture 1:https://example.com/video1.mp4\n"
        "Notes:https://example.com/notes.pdf</code>\n\n"
        "2. Send the file to this bot\n"
        "3. You'll receive a secure HTML file\n"
        "4. To access content, you'll need:\n"
        "   - Your User ID\n"
        "   - The Access Code provided\n\n"
        "🔒 The file cannot be used by anyone else",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]])
    )

@app.on_callback_query(filters.regex("^back$"))
async def back_handler(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{callback.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

# ===== MAIN =====
if __name__ == "__main__":
    print("✅ Secure HTML Bot is running...")
    app.run()
