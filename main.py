import os
import requests
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import ListenerTimeout
from subprocess import getstatusoutput
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Bot credentials
API_ID = int(os.environ.get("API_ID", 21705536))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7286340326:AAEDWRjNnqx7W602n7BPJIm7a0EYMQO4SKQ")

# Thread pool for background tasks
THREADPOOL = ThreadPoolExecutor(max_workers=10)

# Initialize the bot
app = Client("pw_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# API constants
HEADERS = {
    'Host': 'api.penpencil.xyz',
    'client-id': '5eb393ee95fab7468a79d189',
    'client-version': '12.84',
    'user-agent': 'Android',
    'randomid': 'e4307177362e86f1',
    'client-type': 'MOBILE',
    'device-meta': '{APP_VERSION:12.84,DEVICE_MAKE:Asus,DEVICE_MODEL:ASUS_X00TD,OS_VERSION:6,PACKAGE_NAME:xyz.penpencil.physicswalb}',
    'content-type': 'application/json; charset=UTF-8',
}

BASE_PARAMS = {
    'mode': '1',
    'filter': 'false',
    'exam': '',
    'amount': '',
    'organisationId': '5eb393ee95fab7468a79d189',
    'classes': '',
    'limit': '20',
    'page': '1',
    'programId': '',
    'ut': '1652675230446',
}

# Authorization check (placeholder - implement your own logic)
async def is_authorized(user_id: int) -> bool:
    return True  # Replace with actual authorization logic

async def process_pwwp(client: Client, message: Message, user_id: int):
    """Handle Physics Wallah login/auth token process"""
    editable = await message.reply_text(
        "**Enter Working Access Token\n\nOR\n\nEnter Phone Number**"
    )

    try:
        input_msg = await client.listen(
            chat_id=message.chat.id, 
            filters=filters.user(user_id), 
            timeout=120
        )
        raw_text = input_msg.text
        await input_msg.delete()
    except ListenerTimeout:
        await editable.edit("**Timeout! You took too long to respond**")
        return

    login_headers = {
        'Host': 'api.penpencil.co',
        'client-id': '5eb393ee95fab7468a79d189',
        'client-version': '1910',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; M2101K6P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
        'randomid': '72012511-256c-4e1c-b4c7-29d67136af37',
        'client-type': 'WEB',
        'content-type': 'application/json; charset=utf-8',
    }

    loop = asyncio.get_event_loop()    
    connector = aiohttp.TCPConnector(limit=1000, loop=loop)
    
    async with aiohttp.ClientSession(connector=connector, loop=loop) as session:
        try:
            if raw_text.isdigit() and len(raw_text) == 10:
                phone = raw_text
                data = {
                    "username": phone,
                    "countryCode": "+91",
                    "organizationId": "5eb393ee95fab7468a79d189"
                }
                try:
                    async with session.post(
                        "https://api.penpencil.co/v1/users/get-otp?smsType=0", 
                        json=data, 
                        headers=login_headers
                    ) as response:
                        await response.read()
                    
                except Exception as e:
                    await editable.edit(f"**Error : {e}**")
                    return

                editable = await editable.edit("**ENTER OTP YOU RECEIVED**")
                try:
                    otp_msg = await client.listen(
                        chat_id=message.chat.id,
                        filters=filters.user(user_id),
                        timeout=120
                    )
                    otp = otp_msg.text
                    await otp_msg.delete()
                except ListenerTimeout:
                    await editable.edit("**Timeout! You took too long to respond**")
                    return

                payload = {
                    "username": phone,
                    "otp": otp,
                    "client_id": "system-admin",
                    "client_secret": "KjPXuAVfC5xbmgreETNMaL7z",
                    "grant_type": "password",
                    "organizationId": "5eb393ee95fab7468a79d189",
                    "latitude": 0,
                    "longitude": 0
                }

                try:
                    async with session.post(
                        "https://api.penpencil.co/v3/oauth/token", 
                        json=payload, 
                        headers=login_headers
                    ) as response:
                        access_token = (await response.json())["data"]["access_token"]
                        await editable.edit(
                            "<b>Physics Wallah Login Successful ✅</b>\n\n"
                            f"<pre language='Save this Login Token for future usage'>{access_token}</pre>\n\n"
                        )
                        editable = await message.reply_text("**Getting Batches In Your I'd**")
                    
                except Exception as e:
                    await editable.edit(f"**Error : {e}**")
                    return

            else:
                access_token = raw_text
            
            # Now proceed with the download process using the obtained access token
            await handle_download_process(client, message, access_token)
        
        except Exception as e:
            await editable.edit(f"**An error occurred: {str(e)}**")

async def handle_download_process(client: Client, message: Message, access_token: str):
    """Handle the download process after successful authentication"""
    headers = HEADERS.copy()
    headers['authorization'] = f"Bearer {access_token}"
    
    try:
        # Fetch batches
        await message.reply("📡 Fetching your batches...")
        batches = await get_batches(headers)
        if not batches:
            return await message.reply("❌ No batches found or invalid auth token.")
        
        # Display batches
        batch_list = "\n".join([f"`{b['_id']}` : {b['name']}" for b in batches])
        await message.reply(f"📚 Available Batches:\n\n{batch_list}")
        
        # Get batch ID
        batch_msg = await message.reply("🆔 Enter the **Batch ID** you want to download:")
        batch_response = await client.listen(message.chat.id, timeout=300)
        batch_id = batch_response.text.strip()
        
        # Get subjects
        await batch_msg.edit("📡 Fetching subjects...")
        subjects = await get_subjects(headers, batch_id)
        if not subjects:
            return await batch_msg.edit("❌ No subjects found in this batch.")
        
        # Display subjects
        subject_list = "\n".join([f"`{s['_id']}`" for s in subjects])
        await message.reply(f"📖 Available Subjects:\n\n{subject_list}")
        
        # Get subject IDs to download
        subject_msg = await message.reply("📥 Enter subject IDs to download (separated by &):")
        subject_response = await client.listen(message.chat.id, timeout=300)
        subject_ids = [sid.strip() for sid in subject_response.text.split('&') if sid.strip()]
        
        # Get thumbnail
        thumb_msg = await message.reply("🖼️ Send thumbnail URL (or type 'no' to skip):")
        thumb_response = await client.listen(message.chat.id, timeout=300)
        thumb_url = thumb_response.text if thumb_response.text.lower() != 'no' else None
        
        thumb_path = None
        if thumb_url and thumb_url.startswith(('http://', 'https://')):
            try:
                getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
                thumb_path = "thumb.jpg"
            except Exception as e:
                await message.reply(f"⚠️ Failed to download thumbnail: {str(e)}")
        
        # Process download
        batch_name = next((b['name'] for b in batches if b['_id'] == batch_id), "Unknown_Batch")
        output_file = f"{batch_name.replace('/', '_')}.txt"
        
        progress_msg = await message.reply(f"⏳ Downloading content for batch: {batch_name}...")
        
        try:
            with open(output_file, 'w') as f:
                for subject_id in subject_ids:
                    try:
                        content = await get_batch_content(headers, batch_id, subject_id)
                        for item in content:
                            # Process URL
                            url = item['url'].replace("d1d34p8vz63oiq", "d3nzo6itypaz07").replace("mpd", "m3u8").strip()
                            f.write(f"{item['topic']}:{url}\n")
                    except Exception as e:
                        await message.reply(f"⚠️ Error processing subject {subject_id}: {str(e)}")
                        continue
            
            await progress_msg.edit("✅ Download complete!")
            await message.reply_document(
                output_file,
                caption=f"📁 {batch_name} - Download Links",
                thumb=thumb_path
            )
            
        except Exception as e:
            await progress_msg.edit(f"❌ Download failed: {str(e)}")
        finally:
            # Clean up files
            if os.path.exists(output_file):
                os.remove(output_file)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
                
    except Exception as e:
        await message.reply(f"❌ An unexpected error occurred: {str(e)}")

async def get_batches(headers):
    """Fetch available batches from Physics Wallah API"""
    response = requests.get(
        'https://api.penpencil.xyz/v3/batches/my-batches',
        params=BASE_PARAMS,
        headers=headers
    )
    response.raise_for_status()
    return response.json().get("data", [])

async def get_subjects(headers, batch_id):
    """Fetch subjects for a specific batch"""
    response = requests.get(
        f'https://api.penpencil.xyz/v3/batches/{batch_id}/details',
        headers=headers
    )
    response.raise_for_status()
    return response.json().get("data", {}).get("subjects", [])

async def get_batch_content(headers, batch_id, subject_id):
    """Fetch content for a batch subject"""
    content = []
    for page in range(1, 5):  # Check first 4 pages
        params = {
            'page': str(page),
            'tag': '',
            'contentType': 'exercises-notes-videos',
            'ut': ''
        }
        response = requests.get(
            f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents',
            params=params,
            headers=headers
        )
        response.raise_for_status()
        page_content = response.json().get("data", [])
        if not page_content:
            break
        content.extend(page_content)
    return content

@app.on_callback_query(filters.regex("^pw_auth$"))
async def pw_auth_callback(client: Client, callback_query: CallbackQuery):
    """Handle callback for Physics Wallah authentication"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    if not await is_authorized(user_id):
        await callback_query.message.reply("**You Are Not Subscribed To This Bot**")
        return
        
    THREADPOOL.submit(
        asyncio.run_coroutine_threadsafe,
        process_pwwp(client, callback_query.message, user_id),
        asyncio.get_event_loop()
    )

@app.on_message(filters.command(["pw"]))
async def start_pw_download(client: Client, message: Message):
    """Handle the /pw command to initiate Physics Wallah content download"""
    user_id = message.from_user.id
    if not await is_authorized(user_id):
        await message.reply("**You Are Not Subscribed To This Bot**")
        return
    
    await process_pwwp(client, message, user_id)

if __name__ == "__main__":
    print("Starting Physics Wallah Downloader Bot...")
    app.run()
