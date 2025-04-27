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

# Bot credentials from environment variables
API_ID = int(os.environ.get("API_ID", 21705536))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7286340326:AAEDWRjNnqx7W602n7BPJIm7a0EYMQO4SKQ")

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Constants for API requests
API_HEADERS = {
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

CONTENT_PARAMS = {
    'tag': '',
    'contentType': 'exercises-notes-videos',
    'ut': ''
}

@bot.on_message(filters.command(["pw"]))
async def handle_physics_wallah(bot: Client, message: Message):
    """Handle the /pw command to download Physics Wallah content."""
    
    # Step 1: Get authentication token from user
    auth_msg = await message.reply_text(
        "Please send your **Auth code** in this format:\n\n**AUTH CODE**"
    )
    auth_input = await bot.listen(message.chat.id)
    auth_token = auth_input.text
    
    # Add authorization to headers
    headers = API_HEADERS.copy()
    headers['authorization'] = f"Bearer {auth_token}"

    try:
        # Step 2: Fetch available batches
        await auth_msg.edit("**Fetching your batches...**")
        batches_response = requests.get(
            'https://api.penpencil.xyz/v3/batches/my-batches',
            params=BASE_PARAMS,
            headers=headers
        ).json()["data"]
        
        # Display available batches
        await message.reply_text("**Available Batches:**\n\nBatch ID : Batch Name")
        for batch in batches_response:
            batch_info = f"```{batch['name']}``` : ```{batch['_id']}```"
            await message.reply_text(batch_info)
        
        # Step 3: Get batch ID to download
        batch_prompt = await message.reply_text("**Please send the Batch ID you want to download**")
        batch_input = await bot.listen(message.chat.id)
        batch_id = batch_input.text
        
        # Step 4: Get subjects for selected batch
        subjects_response = requests.get(
            f'https://api.penpencil.xyz/v3/batches/{batch_id}/details',
            headers=headers
        ).json()["data"]["subjects"]
        
        # Display subjects
        subject_ids = []
        await message.reply_text("**Available Subjects:**\n\nSubject ID")
        for subject in subjects_response:
            subject_id = subject['_id']
            subject_ids.append(subject_id)
            await message.reply_text(f"{subject_id}&")
        
        # Combine subject IDs for full batch download
        combined_ids = "&".join(subject_ids)
        await message.reply_text(
            f"**To download full batch, use this:**\n```{combined_ids}```"
        )
        
        # Step 5: Get subject IDs to download
        subject_prompt = await message.reply_text("**Paste the subject IDs to download**")
        subject_input = await bot.listen(message.chat.id)
        subjects_to_download = subject_input.text.split('&')
        
        # Step 6: Get resolution (though not currently used in the code)
        await message.reply_text("**Enter resolution (optional)**")
        resolution_input = await bot.listen(message.chat.id)
        resolution = resolution_input.text
        
        # Step 7: Get thumbnail
        thumb_prompt = await message.reply_text(
            "**Send thumbnail URL** (e.g., `https://telegra.ph/file/example.jpg`) or send **no**"
        )
        thumb_input = await bot.listen(message.chat.id)
        thumb_url = thumb_input.text
        
        thumb_path = None
        if thumb_url.startswith(("http://", "https://")):
            getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
            thumb_path = "thumb.jpg"
        
        # Step 8: Process each subject and get content
        batch_name = next((b['name'] for b in batches_response if b['_id'] == batch_id), "Unknown_Batch")
        output_file = f"{batch_name}.txt"
        
        for subject_id in subjects_to_download:
            if not subject_id:
                continue
                
            try:
                # Get content from multiple pages
                for page in range(1, 5):
                    params = CONTENT_PARAMS.copy()
                    params['page'] = str(page)
                    
                    content_response = requests.get(
                        f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents',
                        params=params,
                        headers=headers
                    ).json().get("data", [])
                    
                    # Process each content item
                    for content in content_response:
                        try:
                            title = content["topic"]
                            url = content["url"].replace("d1d34p8vz63oiq", "d3nzo6itypaz07").replace("mpd", "m3u8").strip()
                            
                            with open(output_file, 'a') as f:
                                f.write(f"{title}:{url}\n")
                                
                        except Exception as content_error:
                            logging.error(f"Error processing content: {content_error}")
                            await message.reply_text(f"Error processing content: {content_error}")
                
            except Exception as subject_error:
                logging.error(f"Error processing subject {subject_id}: {subject_error}")
                await message.reply_text(f"Error processing subject {subject_id}: {subject_error}")
        
        # Send the final output file
        await message.reply_document(output_file)
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await message.reply_text(f"An error occurred: {e}")
