import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from subprocess import getstatusoutput
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Bot credentials
API_ID = int(os.environ.get("API_ID", 21705536))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7286340326:AAEDWRjNnqx7W602n7BPJIm7a0EYMQO4SKQ")

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

@app.on_message(filters.command(["pw"]))
async def start_pw_download(client: Client, message: Message):
    """Handle the /pw command to initiate Physics Wallah content download"""
    try:
        # Step 1: Get auth token
        auth_msg = await message.reply("🔑 Please send your Physics Wallah **Auth Token**")
        auth_response = await client.ask(message.chat.id, "Please send your auth token", timeout=300)
        
        if not auth_response.text:
            return await auth_msg.edit("❌ No auth token provided. Command cancelled.")
        
        # Prepare headers with auth token
        headers = HEADERS.copy()
        headers['authorization'] = f"Bearer {auth_response.text}"
        
        # Step 2: Fetch batches
        await auth_msg.edit("📡 Fetching your batches...")
        try:
            batches = await get_batches(headers)
            if not batches:
                return await auth_msg.edit("❌ No batches found or invalid auth token.")
            
            # Display batches
            batch_list = "\n".join([f"`{b['_id']}` : {b['name']}" for b in batches])
            await message.reply(f"📚 Available Batches:\n\n{batch_list}")
            
        except Exception as e:
            return await auth_msg.edit(f"❌ Failed to fetch batches: {str(e)}")
        
        # Step 3: Get batch ID
        batch_msg = await message.reply("🆔 Enter the **Batch ID** you want to download:")
        batch_response = await client.ask(message.chat.id, "Please enter the batch ID", timeout=300)
        batch_id = batch_response.text.strip()
        
        # Step 4: Get subjects
        await batch_msg.edit("📡 Fetching subjects...")
        try:
            subjects = await get_subjects(headers, batch_id)
            if not subjects:
                return await batch_msg.edit("❌ No subjects found in this batch.")
            
            # Display subjects
            subject_list = "\n".join([f"`{s['_id']}`" for s in subjects])
            await message.reply(f"📖 Available Subjects:\n\n{subject_list}")
            
        except Exception as e:
            return await batch_msg.edit(f"❌ Failed to fetch subjects: {str(e)}")
        
        # Step 5: Get subject IDs to download
        subject_msg = await message.reply("📥 Enter subject IDs to download (separated by &):")
        subject_response = await client.ask(message.chat.id, "Please enter subject IDs separated by &", timeout=300)
        subject_ids = [sid.strip() for sid in subject_response.text.split('&') if sid.strip()]
        
        # Step 6: Get thumbnail
        thumb_msg = await message.reply("🖼️ Send thumbnail URL (or type 'no' to skip):")
        thumb_response = await client.ask(message.chat.id, "Please send thumbnail URL or type 'no'", timeout=300)
        thumb_url = thumb_response.text if thumb_response.text.lower() != 'no' else None
        
        thumb_path = None
        if thumb_url and thumb_url.startswith(('http://', 'https://')):
            try:
                getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
                thumb_path = "thumb.jpg"
            except Exception as e:
                await message.reply(f"⚠️ Failed to download thumbnail: {str(e)}")
        
        # Step 7: Process download
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

if __name__ == "__main__":
    print("Starting Physics Wallah Downloader Bot...")
    app.run()
