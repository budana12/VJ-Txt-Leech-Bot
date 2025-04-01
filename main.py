import os
import mmap
import time
import logging
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException, Timeout, ConnectionError
import aiohttp
import aiofiles
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7480080731:AAHJ3jgh7npoAJSZ0tiB2n0bqSY0sp5E4gk"

# Constants
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB Telegram limit
SUPPORTED_VIDEO_EXTENSIONS = ['mp4', 'mkv', 'mov', 'avi', 'webm']
SUPPORTED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for better memory management
DOWNLOAD_TIMEOUT = 300  # 5 minutes timeout
MAX_RETRIES = 5

# Customize these as needed
CR = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚"
my_name = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚"

# Initialize the Pyrogram client
app = Client("file_decryptor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variables to store user data
user_data = {}
stop_flags = {}

async def download_file_async(url, save_path, progress_callback=None):
    """Asynchronous file download with progress tracking"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                total_size = int(response.headers.get('content-length', 0))
                if total_size > MAX_FILE_SIZE:
                    raise ValueError("File too large for Telegram upload")
                
                block_size = CHUNK_SIZE
                downloaded = 0
                
                async with aiofiles.open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(block_size):
                        if chunk:
                            await f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                await progress_callback(downloaded, total_size)
                
                return True
    except Exception as e:
        logger.error(f"Error during async download: {e}")
        raise

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((RequestException, Timeout, ConnectionError))
)
async def download_with_retry(url, save_path, progress_callback=None):
    """Wrapper for download_file_async with retry logic"""
    try:
        return await download_file_async(url, save_path, progress_callback)
    except Exception as e:
        logger.error(f"Download attempt failed: {e}")
        raise

def extract_url_info(line):
    """Extract video name, url and key from a line with validation"""
    if not line:
        return None, None, None
    
    try:
        # Split on first 'http' occurrence
        parts = line.split('http', 1)
        video_name = parts[0].strip(' :')  # Clean name
        url_part = 'http' + parts[1].strip() if len(parts) > 1 else None
        
        if not url_part:
            return None, None, None
        
        # Validate URL structure
        parsed = requests.utils.urlparse(url_part.split('*')[0])
        if not all([parsed.scheme, parsed.netloc]):
            return None, None, None
        
        # Extract key if exists
        if '*' in url_part:
            base_url, key = url_part.split('*', 1)
            return video_name, base_url.strip(), key.strip()
        
        return video_name, url_part.strip(), None
        
    except Exception as e:
        logger.error(f"Error parsing line: {e}")
        return None, None, None

def decrypt_file(file_path, key):
    """Improved decryption function with better error handling"""
    if not os.path.exists(file_path):
        logger.error("Encrypted file not found!")
        return False
    
    try:
        logger.info(f"Decrypting file: {file_path} with key: {key}")
        file_size = os.path.getsize(file_path)
        
        with open(file_path, "r+b") as f:
            # Use memory-mapped file for better performance
            with mmap.mmap(f.fileno(), length=file_size, access=mmap.ACCESS_WRITE) as mmapped_file:
                # Process in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                for offset in range(0, file_size, chunk_size):
                    chunk_end = min(offset + chunk_size, file_size)
                    for i in range(offset, chunk_end):
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
        "👋 Hello! I'm a file download bot.\n\n"
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
    stop_flags[user_id] = False  # Reset stop flag
    
    status_msg = await message.reply_text("📥 Downloading your text file...")
    
    try:
        # Download the text file
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        txt_path = os.path.join(temp_dir, f"links_{user_id}.txt")
        
        await message.download(file_name=txt_path)
        
        # Read the file with better encoding handling
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except UnicodeDecodeError:
            # Fallback to other encodings if UTF-8 fails
            encodings = ['latin1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(txt_path, 'r', encoding=encoding) as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                    break
                except UnicodeDecodeError:
                    continue
        
        if not lines:
            await status_msg.edit_text("❌ The text file is empty.")
            return
        
        # Ask user for start and end range
        await status_msg.edit_text(
            f"📝 Found {len(lines)} links in your file.\n\n"
            f"Please reply with the range you want to download (e.g., '1-10' or '5' for single file)."
        )
        
        # Store user data
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

@app.on_message(filters.text & ~filters.command(["start", "stop"]))
async def handle_range_selection(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        return  # Not in processing mode
    
    if not message.text.strip():
        return
    
    # Parse range input
    try:
        range_input = message.text.strip()
        if '-' in range_input:
            start, end = map(int, range_input.split('-'))
        else:
            start = end = int(range_input)
        
        # Validate range
        lines = user_data[user_id]['lines']
        if start < 1 or end > len(lines) or start > end:
            await message.reply_text(f"❌ Invalid range. Please enter between 1 and {len(lines)}")
            return
        
        processing_msg = await message.reply_text(f"⏳ Starting download from line {start} to {end}...")
        failed_items = []
        success_count = 0
        
        for i in range(start-1, end):  # Convert to 0-based index
            if stop_flags.get(user_id, False):
                await processing_msg.edit_text("🛑 Processing stopped by user")
                stop_flags[user_id] = False  # Reset flag
                break
            
            line = lines[i]
            video_name, url, key = extract_url_info(line)
            count = i + 1  # 1-based index for display
            
            if not url:
                failed_item = {
                    'number': count,
                    'name': video_name,
                    'url': 'Invalid URL format',
                    'error': 'Could not extract valid URL'
                }
                failed_items.append(failed_item)
                await message.reply_text(create_failure_message(failed_item))
                continue
                
            try:
                await processing_msg.edit_text(f"⏳ Downloading #{count}: {video_name or 'Unnamed file'}")
                
                # Create temp paths
                temp_dir = "temp_files"
                encrypted_path = os.path.join(temp_dir, f"temp_{user_id}_{i}.tmp")
                final_path = None
                
                # Download with progress tracking
                try:
                    async def progress_callback(current, total):
                        if total > 0:
                            percentage = (current / total) * 100
                            await processing_msg.edit_text(
                                f"⏳ Downloading #{count}: {video_name or 'Unnamed file'}\n"
                                f"Progress: {percentage:.1f}%"
                            )
                    
                    if not await download_with_retry(url, encrypted_path, progress_callback):
                        raise Exception("Download failed after retries")
                except Exception as e:
                    failed_item = {
                        'number': count,
                        'name': video_name,
                        'url': url,
                        'error': str(e)
                    }
                    failed_items.append(failed_item)
                    await message.reply_text(create_failure_message(failed_item))
                    continue
                
                # Decrypt if key exists
                if key:
                    if not decrypt_file(encrypted_path, key):
                        failed_item = {
                            'number': count,
                            'name': video_name,
                            'url': url,
                            'error': "Decryption failed - invalid key"
                        }
                        failed_items.append(failed_item)
                        await message.reply_text(create_failure_message(failed_item))
                        continue
                
                # Determine file type and extension
                ext = get_file_extension(url)
                res = ""  # Resolution placeholder if needed
                
                if video_name:
                    safe_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '-', '_'))
                    final_filename = f"{safe_name}.{ext}" if ext else safe_name
                else:
                    final_filename = f"file_{count}.{ext}" if ext else f"file_{count}"
                
                final_path = os.path.join(temp_dir, final_filename)
                os.rename(encrypted_path, final_path)
                user_data[user_id]['processed_files'].append(final_path)
                
                # Prepare caption based on file type
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
                
                # Send to user with progress tracking
                try:
                    if ext and is_video_file(ext):
                        await message.reply_document(
                            document=final_path,
                            caption=caption,
                            progress=lambda current, total: logger.info(f"Uploaded {current} of {total} bytes")
                        )
                    elif ext and is_document_file(ext):
                        await message.reply_document(
                            document=final_path,
                            caption=caption,
                            progress=lambda current, total: logger.info(f"Uploaded {current} of {total} bytes")
                        )
                    else:
                        await message.reply_document(
                            document=final_path,
                            caption=caption,
                            progress=lambda current, total: logger.info(f"Uploaded {current} of {total} bytes")
                        )
                    
                    success_count += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    continue
                except Exception as e:
                    failed_item = {
                        'number': count,
                        'name': video_name,
                        'url': url,
                        'error': f"Failed to send file: {str(e)}"
                    }
                    failed_items.append(failed_item)
                    await message.reply_text(create_failure_message(failed_item))
                    continue
                
            except Exception as e:
                logger.error(f"Error processing line {count}: {e}")
                failed_item = {
                    'number': count,
                    'name': video_name,
                    'url': url,
                    'error': str(e)
                }
                failed_items.append(failed_item)
                await message.reply_text(create_failure_message(failed_item))
                continue
        
        # Final message
        await processing_msg.edit_text(f"✅ Finished processing {success_count} files")
        
        # Store failed items
        if failed_items:
            user_data[user_id]['failed_downloads'] = failed_items
        
    except ValueError:
        await message.reply_text("❌ Invalid input. Please enter numbers like '1-10' or '5'")
    except Exception as e:
        logger.error(f"Error in range processing: {e}")
        await message.reply_text(f"❌ Error during processing: {str(e)}")
    finally:
        # Clean up processed files
        if user_id in user_data and 'processed_files' in user_data[user_id]:
            for file_path in user_data[user_id]['processed_files']:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
        stop_flags[user_id] = False  # Reset stop flag

if __name__ == "__main__":
    # Create temp directory if not exists
    os.makedirs("temp_files", exist_ok=True)
    logger.info("Bot is running...")
    app.run()
