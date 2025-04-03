from pyrogram import Client, filters
from pyrogram.types import Message, User
from datetime import datetime

app = Client(
    "my_account",
    api_id="21705536",  # Get from https://my.telegram.org
    api_hash="c5bb241f6e3ecf33fe68a444e288de2d",  # Get from https://my.telegram.org
    bot_token="8193765546:AAEs_Ul-zoQKAto5-I8vYJpGSZgDEa-POeU"  # Get from @BotFather
)

def format_phone_number(phone: str) -> str:
    """Format phone number with country code if available"""
    if not phone:
        return "🚫 Hidden"
    return f"📱 +{phone}" if phone.startswith("+") else f"📱 {phone}"

@app.on_message(filters.command("start"))
async def get_user_details(client: Client, message: Message):
    user = message.from_user
    if not user:
        return await message.reply("❌ Could not fetch user details")
    
    # Get complete user object
    try:
        full_user: User = await client.get_users(user.id)
    except Exception as e:
        print(f"Error getting full user: {e}")
        full_user = user
    
    # Prepare all possible details
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
        ("📝 Bio", (await client.get_chat(user.id)).bio or "🚫 None"),
        ("📱 Last Seen", datetime.fromtimestamp(full_user.last_online_date).strftime('%Y-%m-%d %H:%M:%S') if hasattr(full_user, 'last_online_date') else "🚫 Hidden"),
        ("🎂 Birthday", str(full_user.birthday) if hasattr(full_user, 'birthday') else "🚫 Not set"),
        ("🌍 Data Center", f"DC {full_user.dc_id}" if hasattr(full_user, 'dc_id') else "🚫 Unknown"),
    ]
    
    # Format the message
    details_message = "🔍 <b>Telegram User Details</b> 🔍\n\n"
    details_message += "\n".join(f"• {emoji} {field}: {value}" for emoji, field, value in details)
    
    await message.reply_text(details_message)

app.run()
