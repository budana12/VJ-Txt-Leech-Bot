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
    
    # Basic details always available
    details = {
        "🆔 User ID": user.id,
        "👤 Username": f"@{user.username}" if user.username else "None",
        "👔 First Name": user.first_name,
        "👖 Last Name": user.last_name if user.last_name else "None",
        "📛 Full Name": user.first_name + (" " + user.last_name if user.last_name else ""),
        "🤖 Is Bot": "Yes" if user.is_bot else "No",
        "🌐 Language Code": user.language_code if user.language_code else "None",
        "💎 Telegram Premium": "Yes" if user.is_premium else "No",
        "🔒 Restricted": "Yes" if user.is_restricted else "No",
        "✅ Verified": "Yes" if user.is_verified else "No",
        "❌ Scam": "Yes" if user.is_scam else "No",
        "🚫 Fake": "Yes" if user.is_fake else "No"
    }
    
    # Try to get more sensitive details
    try:
        full_user = await client.get_users(user.id)
        more_details = {
            "📞 Phone Number": full_user.phone_number if hasattr(full_user, 'phone_number') else "Hidden",
            "📅 Account Creation Date": datetime.fromtimestamp(full_user.date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'date') else "Unknown",
            "🖼️ Profile Photo": "Yes" if full_user.photo else "No",
            "📝 Bio": (await client.get_chat(full_user.id)).bio if (await client.get_chat(full_user.id)).bio else "None",
            "📱 Last Online": datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'last_online_date') else "Hidden",
            "🎂 Birthday": full_user.birthday if hasattr(full_user, 'birthday') else "Not set",
            "🌍 DC ID": full_user.dc_id if hasattr(full_user, 'dc_id') else "Unknown"
        }
        details.update(more_details)
    except Exception as e:
        print(f"Couldn't get additional details: {e}")
    
    # Format the message
    details_message = "🔍 <b>Telegram User Details:</b>\n\n"
    for key, value in details.items():
        if value and str(value).lower() not in ["none", "hidden", "unknown", "not set"]:
            details_message += f"• <b>{key}:</b> {value}\n"
    
    await message.reply_text(details_message, parse_mode="HTML")  # Changed to uppercase

app.run()
