#!/usr/bin/env python3
import os
import mmap
import time
import logging
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration (replace with your values)
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "8193765546:AAEs_Ul-zoQKAto5-I8vYJpGSZgDEa-POeU"

# Constants
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB Telegram limit
SUPPORTED_VIDEO_EXTENSIONS = ['mp4', 'mkv', 'mov', 'avi', 'webm']
SUPPORTED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']
MAX_CONCURRENT_DOWNLOADS = 4  # Number of parallel downloads
ARIA2_CONNECTIONS = 16  # Connections per download

# Customize these as needed
CR = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚"  # Credit/Extracted By
my_name = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚"  # Your name for captions

# Initialize the Pyrogram client
app = Client("file_decryptor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variables to store user data
user_data = {}
stop_flags = {}

def download_with_aria2(url, save_path):
    """Download file using aria2 with multiple connections"""
    try:
        logger.info(f"Starting aria2 download for: {url}")
        
        command = [
            'aria2c',
            url,
            '-o', save_path,
            '-x', str(ARIA2_CONNECTIONS),
            '-s', str(ARIA2_CONNECTIONS),
            '-j', str(ARIA2_CONNECTIONS),
            '--max-tries=5',
            '--retry-wait=5',
            '--timeout=60',
            '--connect-timeout=60',
            '--check-certificate=false',
            '--allow-overwrite=true',
            '--auto-file-renaming=false',
            '--quiet'
        ]
        
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"aria2 download failed: {result.stderr}")
            return False
            
        logger.info(f"Download completed successfully to: {save_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"aria2 download error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error in aria2 download: {str(e)}")
        return False

def extract_url_info(line):
    """Extract video name, url and key from a line with validation"""
    if not line or 'http' not in line:
        return None, None, None
    
    try:
        parts = line.split('http', 1)
        video_name = parts[0].strip(' :')
        url_part = 'http' + parts[1].strip() if len(parts) > 1 else None
        
        if not url_part:
            return None, None, None
        
        parsed = requests.utils.urlparse(url_part.split('*')[0])
        if not all([parsed.scheme, parsed.netloc]):
            return None, None, None
        
        if '*' in url_part:
            base_url, key = url_part.split('*', 1)
            return video_name, base_url.strip(), key.strip()
        
        return video_name, url_part.strip(), None
        
    except Exception as e:
        logger.error(f"Error parsing line: {e}")
        return None, None, None

def decrypt_file(file_path, key):
    if not os.path.exists(file_path):
        logger.error("Encrypted file not found!")
        return False
    
    try:
        logger.info(f"Decrypting file: {file_path} with key: {key}")
        with open(file_path, "r+b") as f:
            num_bytes = min(28, os.path.getsize(file_path))
            with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:
                for i in range(num_bytes):
                    mmapped_file[i] ^= ord(key[i % len(key)])
        logger.info("Decryption completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error during decryption: {e}")
        return False

def get_file_extension(url):
    """Extract file extension from URL"""
    filename = url.split('?')[0].split('#')[0].split('/')[-1]
    if '.' in filename:
        return filename.split('.')[-1].lower()
    return None

def is_video_file(extension):
    return extension in SUPPORTED_VIDEO_EXTENSIONS

def is_document_file(extension):
    return extension in SUPPORTED_DOCUMENT_EXTENSIONS

def create_failure_message(item):
    """Create a formatted failure message for a single item"""
    message = "❌ Download Failed\n\n"
    message += f"🔢 File Number: #{item['number']}\n"
    message += f"📛 Name: {item['name'] or 'Unnamed'}\n"
    message += f"🔗 URL: {item['url']}\n"
    message += f"❗ Error: {item['error']}\n"
    return message

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 Hello! I'm a file download bot with aria2 integration.\n\n"
        "📁 Upload a .txt file containing your links in this format:\n\n"
        "`Video Name:https://example.com/encrypted.mp4*mysecretkey`\n\n"
        "Or simply:\n"
        "`Video Name:https://example.com/file.mp4`\n\n"
        "Each link should be on a new line. I'll process all valid links.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/stop - Stop current processing"
    )

@app.on_message(filters.command("stop"))
async def stop_command(client: Client, message: Message):
    user_id = message.from_user.id
    stop_flags[user_id] = True
    await message.reply_text("🛑 Stopping current processing...")
    logger.info(f"User {user_id} requested to stop processing")

@app.on_message(filters.document)
async def handle_txt_file(client: Client, message: Message):
    if not message.document.file_name.endswith('.txt'):
        await message.reply_text("❌ Please upload a .txt file containing your links.")
        return
    
    user_id = message.from_user.id
    stop_flags[user_id] = False
    
    status_msg = await message.reply_text("📥 Downloading your text file...")
    
    try:
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        txt_path = os.path.join(temp_dir, f"links_{user_id}.txt")
        
        await message.download(file_name=txt_path)
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines:
            await status_msg.edit_text("❌ The text file is empty.")
            return
        
        await status_msg.edit_text(
            f"📝 Found {len(lines)} links in your file.\n\n"
            f"Please reply with the range you want to download (e.g., '1-10' or '5' for single file)."
        )
        
        user_data[user_id] = {
            'txt_path': txt_path,
            'lines': lines,
            'processed_files': [],
            'failed_downloads': []
        }
        
    except Exception as e:
        logger.error(f"Error processing text file: {e}")
        await message.reply_text(f"❌ Error processing file: {str(e)}")
        if 'status_msg' in locals():
            await status_msg.delete()

async def process_single_download(client, message, user_id, idx):
    """Process a single download item"""
    line = user_data[user_id]['lines'][idx]
    video_name, url, key = extract_url_info(line)
    count = idx + 1
    
    if not url:
        failed_item = {
            'number': count,
            'name': video_name,
            'url': 'Invalid URL format',
            'error': 'Could not extract valid URL'
        }
        user_data[user_id]['failed_downloads'].append(failed_item)
        await message.reply_text(create_failure_message(failed_item))
        return False
        
    try:
        temp_dir = "temp_files"
        encrypted_path = os.path.join(temp_dir, f"temp_{user_id}_{idx}.tmp")
        
        # Download with aria2
        if not download_with_aria2(url, encrypted_path):
            raise Exception("Download failed after retries")
            
        # Decrypt if key exists
        if key:
            if not decrypt_file(encrypted_path, key):
                raise Exception("Decryption failed - invalid key")
        
        # Determine file type and extension
        ext = get_file_extension(url)
        res = ""
        
        if video_name:
            safe_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '-', '_'))
            final_filename = f"{safe_name}.{ext}" if ext else safe_name
        else:
            final_filename = f"file_{count}.{ext}" if ext else f"file_{count}"
        
        final_path = os.path.join(temp_dir, final_filename)
        os.rename(encrypted_path, final_path)
        user_data[user_id]['processed_files'].append(final_path)
        
        # Prepare caption
        name1 = video_name or f"File {count}"
        
        if ext and is_video_file(ext):
            caption = (
                f"**🎞️ VID_ID: {str(count).zfill(3)}.\n\n"
                f"📝 Title: {name1} {my_name} {res}.mkv\n\n"
                f"📥 Extracted By : {CR}\n\n"
                f"**━━━━━✦{my_name}✦━━━━━**"
            )
        elif ext and is_document_file(ext):
            caption = (
                f"**📁 PDF_ID: {str(count).zfill(3)}.\n\n"
                f"📝 Title: {name1} {my_name}.pdf\n\n"
                f"📥 Extracted By : {CR}\n\n"
                f"**━━━━━✦{my_name}✦━━━━━**"
            )
        else:
            caption = f"File #{count}: {name1}"
        
        # Send to user
        try:
            if ext and is_video_file(ext):
                await message.reply_document(
                    document=final_path,
                    caption=caption
                )
            elif ext and is_document_file(ext):
                await message.reply_document(
                    document=final_path,
                    caption=caption
                )
            else:
                await message.reply_document(
                    document=final_path,
                    caption=caption
                )
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return False
        except Exception as e:
            raise Exception(f"Failed to send file: {str(e)}")
            
    except Exception as e:
        failed_item = {
            'number': count,
            'name': video_name,
            'url': url,
            'error': str(e)
        }
        user_data[user_id]['failed_downloads'].append(failed_item)
        await message.reply_text(create_failure_message(failed_item))
        return False

@app.on_message(filters.text & ~filters.command(["start", "stop"]))
async def handle_range_selection(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        return
    
    if not message.text.strip():
        return
    
    try:
        range_input = message.text.strip()
        if '-' in range_input:
            start, end = map(int, range_input.split('-'))
        else:
            start = end = int(range_input)
        
        lines = user_data[user_id]['lines']
        if start < 1 or end > len(lines) or start > end:
            await message.reply_text(f"❌ Invalid range. Please enter between 1 and {len(lines)}")
            return
        
        processing_msg = await message.reply_text(f"⏳ Starting download from line {start} to {end}...")
        success_count = 0
        
        # Process downloads in parallel with limited concurrency
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        
        async def process_item(idx):
            nonlocal success_count
            async with semaphore:
                if stop_flags.get(user_id, False):
                    return
                
                await processing_msg.edit_text(f"⏳ Downloading #{idx+1}: {user_data[user_id]['lines'][idx].split(':')[0] or 'Unnamed file'}")
                if await process_single_download(client, message, user_id, idx):
                    success_count += 1
        
        tasks = [process_item(i) for i in range(start-1, end)]
        await asyncio.gather(*tasks)
        
        # Final message
        await processing_msg.edit_text(f"✅ Finished processing {success_count} files")
        
        # Clean up processed files
        if user_id in user_data and 'processed_files' in user_data[user_id]:
            for file_path in user_data[user_id]['processed_files']:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
        
        # Report failures if any
        if user_data[user_id]['failed_downloads']:
            failed_count = len(user_data[user_id]['failed_downloads'])
            await message.reply_text(f"⚠️ {failed_count} downloads failed. Check previous messages for details.")
        
        stop_flags[user_id] = False
        
    except ValueError:
        await message.reply_text("❌ Invalid input. Please enter numbers like '1-10' or '5'")
    except Exception as e:
        logger.error(f"Error in range processing: {e}")
        await message.reply_text(f"❌ Error during processing: {str(e)}")

if __name__ == "__main__":
    # Create temp directory if not exists
    os.makedirs("temp_files", exist_ok=True)
    logger.info("Bot is running with aria2 integration...")
    app.run()
