import os
import requests
import hashlib
import secrets
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# Bot configuration
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8193765546:AAEs_Ul-zoQKAto5-I8vYJpGSZgDEa-POeU"
DEFAULT_THUMBNAIL = "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
SECRET_KEY = "kfskjhfsdcnnsfsncnsdk"  # IMPORTANT: Change this!

app = Client("secure_html_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Utility functions
def generate_user_token(user_id):
    return hashlib.sha256(f"{user_id}{SECRET_KEY}".encode()).hexdigest()

def generate_access_code():
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def format_phone_number(phone):
    if not phone:
        return "🚫 Hidden"
    return f"📞 {phone[:4]}****{phone[-3:]}"

async def get_user_details(client, user):
    try:
        full_user = await client.get_users(user.id)
    except Exception:
        full_user = user
    
    details = [
        ("🆔 User ID", str(user.id)),
        ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
        ("👔 First Name", user.first_name or "🚫 None"),
        ("👖 Last Name", user.last_name or "🚫 None"),
        ("📛 Full Name", f"{user.first_name or ''} {user.last_name or ''}".strip() or "🚫 None"),
        ("🤖 Bot Account", "✅ Yes" if user.is_bot else "❌ No"),
        ("🌐 Language", user.language_code or "🚫 Unknown"),
        ("💎 Premium", "✨ Yes" if user.is_premium else "❌ No"),
        ("🔐 Restricted", "🔒 Yes" if user.is_restricted else "🔓 No"),
        ("✅ Verified", "☑️ Yes" if user.is_verified else "❌ No"),
        ("⚠️ Scam", "🚨 Yes" if user.is_scam else "✅ No"),
        ("🚫 Fake", "❌ Yes" if user.is_fake else "✅ No"),
        ("📅 Account Created", datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date') else "🚫 Unknown"),
        ("📞 Phone Number", format_phone_number(getattr(full_user, 'phone_number', None))),
        ("🖼️ Profile Photo", "🖼️ Yes" if user.photo else "🚫 No"),
        ("📝 Bio", getattr(full_user, 'bio', "🚫 None")),
        ("📱 Last Seen", datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'last_online_date') else "🚫 Hidden"),
        ("🎂 Birthday", str(full_user.birthday) if hasattr(full_user, 'birthday') else "🚫 Not set"),
        ("🌍 Data Center", f"DC {full_user.dc_id}" if hasattr(full_user, 'dc_id') else "🚫 Unknown"),
    ]
    return details

def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
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

def generate_html(file_name, videos, pdfs, others, user_id, access_code, user_details):
    base_name = os.path.splitext(file_name)[0]
    
    # Generate user details HTML
    details_html = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{label}:</span> <span class="detail-value">{value}</span></div>'
        for label, value in user_details
    )
    
    # Generate content links
    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="{url}" target="_blank">{name}</a> <a href="{url}" download>📥 Download PDF</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in others)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }}
        body {{ background: #f5f7fa; text-align: center; }}
        
        /* Auth modal styles */
        .auth-modal {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }}
        .auth-content {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 400px;
            width: 90%;
        }}
        .auth-content input {{
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .auth-content button {{
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .error-message {{
            color: red;
            margin-top: 10px;
            display: none;
        }}
        
        /* User details section */
        .user-details {{
            background: white;
            padding: 20px;
            margin: 20px auto;
            max-width: 600px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: left;
        }}
        .detail-item {{
            margin: 10px 0;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        .detail-label {{
            font-weight: bold;
            color: #007bff;
        }}
        .detail-value {{
            float: right;
        }}
        
        /* Original styles remain unchanged */
        .header {{ background: linear-gradient(90deg, #007bff, #6610f2); color: white; padding: 15px; font-size: 24px; font-weight: bold; }}
        .subheading {{ font-size: 18px; margin-top: 10px; color: #555; font-weight: bold; }}
        .subheading a {{ background: linear-gradient(90deg, #ff416c, #ff4b2b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-decoration: none; font-weight: bold; }}
        .container {{ display: flex; justify-content: space-around; margin: 30px auto; width: 80%; }}
        .tab {{ flex: 1; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; transition: 0.3s; border-radius: 10px; font-size: 20px; font-weight: bold; }}
        .tab:hover {{ background: #007bff; color: white; }}
        .content {{ display: none; margin-top: 20px; }}
        .content.active {{ display: block; }}
        .footer {{ margin-top: 30px; font-size: 18px; font-weight: bold; padding: 15px; background: #1c1c1c; color: white; border-radius: 10px; }}
        .footer a {{ color: #ffeb3b; text-decoration: none; font-weight: bold; }}
        .video-list, .pdf-list, .other-list {{ text-align: left; max-width: 600px; margin: auto; }}
        .video-list a, .pdf-list a, .other-list a {{ display: block; padding: 10px; background: #fff; margin: 5px 0; border-radius: 5px; text-decoration: none; color: #007bff; font-weight: bold; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }}
        .video-list a:hover, .pdf-list a:hover, .other-list a:hover {{ background: #007bff; color: white; }}
        .search-bar {{ margin: 20px auto; width: 80%; max-width: 600px; }}
        .search-bar input {{ width: 100%; padding: 10px; border: 2px solid #007bff; border-radius: 5px; font-size: 16px; }}
        .no-results {{ color: red; font-weight: bold; margin-top: 20px; display: none; }}
        #video-player {{ display: none; margin: 20px auto; width: 80%; max-width: 800px; }}
        #youtube-player {{ display: none; margin: 20px auto; width: 80%; max-width: 800px; }}
        .download-button {{ margin-top: 10px; text-align: center; }}
        .download-button a {{ background: #007bff; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; }}
        .download-button a:hover {{ background: #0056b3; }}
        .datetime {{ margin-top: 10px; font-size: 18px; font-weight: bold; color: #2F4F4F; }}
    </style>
</head>
<body>
    <!-- Auth Modal -->
    <div id="authModal" class="auth-modal">
        <div class="auth-content">
            <h2 style="text-align: center;">🔒 Secure Access</h2>
            <input type="text" id="userIdInput" placeholder="Your User ID">
            <input type="text" id="accessCodeInput" placeholder="Access Code">
            <button onclick="verifyAccess()">Verify</button>
            <p id="errorMessage" class="error-message">Invalid credentials</p>
        </div>
    </div>

    <!-- Main Content (hidden until auth) -->
    <div id="mainContent" style="display: none;">
        <div class="header">{base_name}</div>
        <div class="subheading">📥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 : <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div><br>
        <div class="datetime" id="datetime">📅 {datetime.now().strftime('%A %d %B, %Y | ⏰ %I:%M:%S %p')}</div><br>
        <p>🔹𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭 𝐟𝐨𝐫 𝐓𝐗𝐓 𝐭𝐨 𝐇𝐓𝐌𝐋 𝐟𝐢𝐥𝐞 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 : <a href="https://t.me/htmldeveloperbot" target="_blank"> @𝐡𝐭𝐦𝐥𝐝𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫𝐛𝐨𝐭 </a></p>

        <!-- User Details Section -->
        <div class="user-details">
            <h3 style="text-align: center; margin-bottom: 15px;">👤 User Information</h3>
            {details_html}
        </div>

        <!-- Rest of original content -->
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for videos, PDFs, or other resources..." oninput="filterContent()">
        </div>

        <div id="noResults" class="no-results">No results found.</div>

        <div id="video-player">
            <video id="engineer-babu-player" class="video-js vjs-default-skin" controls preload="auto" width="640" height="360">
                <p class="vjs-no-js">
                    To view this video please enable JavaScript, and consider upgrading to a web browser that
                    <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a>
                </p>
            </video>
            <div class="download-button">
                <a id="download-link" href="#" download>Download Video</a>
            </div>
            <div style="text-align: center; margin-top: 10px; font-weight: bold; color: #007bff;">Engineer Babu Player</div>
        </div>

        <div id="youtube-player">
            <div id="player"></div>
            <div style="text-align: center; margin-top: 10px; font-weight: bold; color: #007bff;">Engineer Babu Player</div>
        </div>

        <div class="container">
            <div class="tab" onclick="showContent('videos')">Videos</div>
            <div class="tab" onclick="showContent('pdfs')">PDFs</div>
            <div class="tab" onclick="showContent('others')">Others</div>
        </div>

        <div id="videos" class="content active">
            <h2>All Video Lectures</h2>
            <div class="video-list">
                {video_links}
            </div>
        </div>

        <div id="pdfs" class="content">
            <h2>All PDFs</h2>
            <div class="pdf-list">
                {pdf_links}
            </div>
        </div>

        <div id="others" class="content">
            <h2>Other Resources</h2>
            <div class="other-list">
                {other_links}
            </div>
        </div>

        <div class="footer">Extracted By - <a href="https://t.me/Engineers_Babu" target="_blank">Engineer Babu</a></div>
    </div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        // Authentication data
        const REQUIRED_USER_ID = "{user_id}";
        const ACCESS_CODE = "{access_code}";
        
        // Check existing auth
        function checkAuth() {{
            const authData = localStorage.getItem('authData');
            if (authData) {{
                try {{
                    const {{ userId, code }} = JSON.parse(authData);
                    if (userId === REQUIRED_USER_ID && code === ACCESS_CODE) {{
                        document.getElementById('authModal').style.display = 'none';
                        document.getElementById('mainContent').style.display = 'block';
                        return true;
                    }}
                }} catch (e) {{
                    console.error('Error parsing auth data:', e);
                }}
            }}
            return false;
        }}
        
        // Verify access
        function verifyAccess() {{
            const userId = document.getElementById('userIdInput').value;
            const code = document.getElementById('accessCodeInput').value;
            
            if (userId === REQUIRED_USER_ID && code === ACCESS_CODE) {{
                // Store auth data
                localStorage.setItem('authData', JSON.stringify({{
                    userId: REQUIRED_USER_ID,
                    code: ACCESS_CODE
                }}));
                
                // Show content
                document.getElementById('authModal').style.display = 'none';
                document.getElementById('mainContent').style.display = 'block';
                document.getElementById('errorMessage').style.display = 'none';
            }} else {{
                document.getElementById('errorMessage').style.display = 'block';
            }}
        }}
        
        // Initialize auth check
        if (!checkAuth()) {{
            document.getElementById('authModal').style.display = 'flex';
        }}
        
        // Original functions remain unchanged
        const player = videojs('engineer-babu-player', {{
            controls: true,
            autoplay: true,
            preload: 'auto',
            fluid: true,
        }});

        let youtubePlayer;

        function onYouTubeIframeAPIReady() {{
            youtubePlayer = new YT.Player('player', {{
                height: '360',
                width: '640',
                events: {{
                    'onReady': onPlayerReady,
                }}
            }});
        }}

        function onPlayerReady(event) {{
            // You can add additional functionality here if needed
        }}

        function playVideo(url) {{
            if (
                url.includes('.m3u8') ||
                url.includes('.mp4') ||
                url.includes('.mkv') ||
                url.includes('.webm') ||
                url.includes('.MP4') ||
                url.includes('.AVI') ||
                url.includes('.MOV') ||
                url.includes('.WMV') ||
                url.includes('.MKV') ||
                url.includes('.FLV') ||
                url.includes('.MPEG') ||
                url.includes('.mpd')
            ) {{
                document.getElementById('video-player').style.display = 'block';
                document.getElementById('youtube-player').style.display = 'none';
                const mimeType = getMimeType(url);
                player.src({{ src: url, type: mimeType }});
                player.play().catch(() => {{
                    window.open(url, '_blank');
                }});
                document.getElementById('download-link').href = url;
            }} else if (url.includes('youtube.com') || url.includes('youtu.be')) {{
                document.getElementById('video-player').style.display = 'none';
                document.getElementById('youtube-player').style.display = 'block';
                youtubePlayer.loadVideoByUrl(url);
            }} else {{
                window.open(url, '_blank');
            }}
        }}

        function getMimeType(url) {{
            if (url.includes('.m3u8')) {{
                return 'application/x-mpegURL';
            }} else if (url.includes('.mp4')) {{
                return 'video/mp4';
            }} else if (url.includes('.mkv')) {{
                return 'video/x-matroska';
            }} else if (url.includes('.webm')) {{
                return 'video/webm';
            }} else if (url.includes('.avi')) {{
                return 'video/x-msvideo';
            }} else if (url.includes('.mov')) {{
                return 'video/quicktime';
            }} else if (url.includes('.wmv')) {{
                return 'video/x-ms-wmv';
            }} else if (url.includes('.flv')) {{
                return 'video/x-flv';
            }} else if (url.includes('.mpeg')) {{
                return 'video/mpeg';
            }} else if (url.includes('.mpd')) {{
                return 'application/dash+xml';
            }} else {{
                return 'video/mp4';
            }}
        }}

        function showContent(tabName) {{
            const contents = document.querySelectorAll('.content');
            contents.forEach(content => {{
                content.classList.remove('active');
                content.style.display = 'none';
            }});
            const selectedContent = document.getElementById(tabName);
            if (selectedContent) {{
                selectedContent.classList.add('active');
                selectedContent.style.display = 'block';
            }}
            filterContent();
        }}

        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const activeTab = document.querySelector('.content.active') || document.getElementById('videos');
            const activeTabId = activeTab.id;
            let hasResults = false;

            let items;
            if (activeTabId === 'videos') {{
                items = document.querySelectorAll('#videos .video-list a');
            }} else if (activeTabId === 'pdfs') {{
                items = document.querySelectorAll('#pdfs .pdf-list a');
            }} else if (activeTabId === 'others') {{
                items = document.querySelectorAll('#others .other-list a');
            }}

            if (items) {{
                items.forEach(item => {{
                    let itemText;
                    if (activeTabId === 'videos') {{
                        itemText = item.textContent.toLowerCase();
                    }} else if (activeTabId === 'pdfs') {{
                        itemText = item.textContent.split('📥')[0].toLowerCase().trim();
                    }} else {{
                        itemText = item.textContent.toLowerCase();
                    }}

                    if (itemText.includes(searchTerm)) {{
                        item.style.display = 'block';
                        hasResults = true;
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});
            }}

            const noResultsMessage = document.getElementById('noResults');
            if (noResultsMessage) {{
                noResultsMessage.style.display = hasResults ? 'none' : 'block';
            }}
        }}

        function updateDateTime() {{
            const now = new Date();
            const options = {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }};
            const formattedDateTime = now.toLocaleDateString('en-US', options);
            document.getElementById('datetime').innerText = `📅 ${{formattedDateTime}}`;
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            showContent('videos');
            setInterval(updateDateTime, 1000);
        }});
    </script>
</body>
</html>"""
    return html_content

# Telegram handlers
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "🔒 Secure HTML Generator Bot\n\n"
        "Send me a .txt file with content in format:\n"
        "<code>Name:URL</code>\n\n"
        f"Your User ID: <code>{message.from_user.id}</code>\n"
        "This ID will be required to access your generated files.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Help", callback_data="help")]])
    )

@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("Please upload a .txt file.")
        return

    user = message.from_user
    user_id = user.id
    
    # Generate access code
    access_code = generate_access_code()
    
    # Get user details
    try:
        user_details = await get_user_details(client, user)
    except Exception as e:
        print(f"Error getting user details: {e}")
        user_details = [
            ("🆔 User ID", str(user.id)),
            ("👤 Username", f"@{user.username}" if user.username else "🚫 None"),
            ("👔 First Name", user.first_name or "🚫 None"),
            ("👖 Last Name", user.last_name or "🚫 None")
        ]

    # Download and process file
    file_path = await message.download()
    file_name = message.document.file_name
    html_path = ""
    
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            file_content = f.read()

        urls = extract_names_and_urls(file_content)
        videos, pdfs, others = categorize_urls(urls)

        # Generate HTML
        html_content = generate_html(file_name, videos, pdfs, others, user_id, access_code, user_details)
        html_path = file_path.replace(".txt", ".html")
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(html_content)

        # Prepare caption
        caption = f"""🔐 Secure HTML File\n\n"""
        caption += "\n".join(f"{label}: {value}" for label, value in user_details[:4])
        caption += f"\n\n🔑 Access Code: <code>{access_code}</code>\n\n"
        caption += "⚠️ Important:\n"
        caption += "1. Do NOT share this file with anyone\n"
        caption += "2. The access code will be required to view content\n"
        caption += "3. The file is tied to your User ID only"

        # Download thumbnail
        thumbnail_path = None
        try:
            thumbnail_response = requests.get(DEFAULT_THUMBNAIL, timeout=10)
            if thumbnail_response.status_code == 200:
                thumbnail_path = "thumbnail.jpg"
                with open(thumbnail_path, "wb") as f:
                    f.write(thumbnail_response.content)
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")

        # Send to user
        await message.reply_document(
            document=html_path,
            file_name=f"secure_{os.path.splitext(file_name)[0]}.html",
            caption=caption,
            thumb=thumbnail_path if thumbnail_path else None
        )

    except Exception as e:
        await message.reply_text(f"❌ Error processing file: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        if html_path and os.path.exists(html_path):
            os.remove(html_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

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

if __name__ == "__main__":
    print("✅ Secure HTML Bot is running...")
    app.run()
