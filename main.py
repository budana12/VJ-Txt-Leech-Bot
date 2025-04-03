from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

app = Client(
    "my_account",
    api_id="21705536",  # Get from https://my.telegram.org
    api_hash="c5bb241f6e3ecf33fe68a444e288de2d",  # Get from https://my.telegram.org
    bot_token="8193765546:AAEs_Ul-zoQKAto5-I8vYJpGSZgDEa-POeU"  # Get from @BotFather
)

@app.on_message(filters.command("start"))
async def get_user_details(client: Client, message: Message):
    user = message.from_user
    
    # Basic details
    details = {
        "🆔 User ID": user.id,
        "👤 Username": f"@{user.username}" if user.username else "None",
        "👔 First Name": user.first_name,
        "👖 Last Name": user.last_name if user.last_name else "None",
        "📛 Full Name": user.first_name + (" " + user.last_name if user.last_name else ""),
        "🤖 Is Bot": "Yes" if user.is_bot else "No",
        "🌐 Language Code": user.language_code if user.language_code else "None",
        "📞 Phone Number": user.phone_number if hasattr(user, 'phone_number') and user.phone_number else "Hidden",
        "💎 Telegram Premium": "Yes" if user.is_premium else "No",
        "🔒 Restricted": "Yes" if user.is_restricted else "No",
        "✅ Verified": "Yes" if user.is_verified else "No",
        "❌ Scam": "Yes" if user.is_scam else "No",
        "🚫 Fake": "Yes" if user.is_fake else "No",
        "📅 Account Creation Date": datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date') else "Unknown",
        "🖼️ Profile Photo": "Yes" if user.photo else "No",
        "📝 Bio": (await client.get_chat(user.id)).bio if (await client.get_chat(user.id)).bio else "None",
        "👥 Common Chats": len(await client.get_common_chats(user.id)) if hasattr(user, 'get_common_chats') else "Unknown"
    }
    
    # Format the details message
    details_message = "🔍 <b>Telegram User Details:</b>\n\n"
    for key, value in details.items():
        details_message += f"• <b>{key}:</b> {value}\n"
    
    # Add DC information if available
    if hasattr(user, 'dc_id'):
        details_message += f"\n🌍 <b>Data Center:</b> DC {user.dc_id}"
    
    await message.reply_text(details_message, parse_mode="html")

    # Try to get more details via get_users
    try:
        full_user = await client.get_users(user.id)
        if full_user:
            extra_details = {
                "📱 Last Online": datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'last_online_date') else "Hidden",
                "📅 Birthday": full_user.birthday if hasattr(full_user, 'birthday') else "Not set",
                "🏙️ Personal Channel": f"@{full_user.personal_channel.username}" if hasattr(full_user, 'personal_channel') and full_user.personal_channel else "None"
            }
            
            extra_message = "\n\n🔎 <b>Additional Details:</b>\n"
            for key, value in extra_details.items():
                if value != "Not set" and value != "Hidden":
                    extra_message += f"• <b>{key}:</b> {value}\n"
            
            await message.reply_text(extra_message, parse_mode="html")
    except Exception as e:
        print(f"Couldn't get extra details: {e}")

app.run()
