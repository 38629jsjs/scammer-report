import os
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
OWNER_ID = 8702798367  # 👈 REPLACE WITH YOUR TELEGRAM ID
PRIVATE_GROUP_ID = -5102493004  # 👈 REPLACE WITH YOUR PRIVATE GROUP ID

user_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Temporary storage for user states and language preferences
user_data = {} # {user_id: {'lang': 'kh', 'state': 'idle', 'report_info': {}}}

def get_text(uid, kh_text, en_text):
    lang = user_data.get(uid, {}).get('lang', 'kh')
    return kh_text if lang == 'kh' else en_text

def get_main_buttons(uid):
    return [
        [Button.text(get_text(uid, "🔍 ពិនិត្យជនខិលខូច", "🔍 Check Scammer"), resize=True),
         Button.text(get_text(uid, "📢 រាយការណ៍អ្នកបោក", "📢 Report Scammer"))],
        [Button.text(get_text(uid, "🌐 ប្តូរភាសា (Language)", "🌐 Change Language"))]
    ]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    if uid not in user_data:
        user_data[uid] = {'lang': 'kh', 'state': 'idle', 'report_info': {}}
    
    await event.respond(
        get_text(uid, "សូមស្វាគមន៍មកកាន់ Vinzy Store Scammer Bot", "Welcome to Vinzy Store Scammer Bot"),
        buttons=get_main_buttons(uid)
    )

@bot.on(events.NewMessage)
async def handle_messages(event):
    uid = event.sender_id
    text = event.text
    if uid not in user_data: user_data[uid] = {'lang': 'kh', 'state': 'idle', 'report_info': {}}

    # --- MENU NAVIGATION ---
    if text in ["🔍 ពិនិត្យជនខិលខូច", "🔍 Check Scammer"]:
        user_data[uid]['state'] = 'awaiting_id'
        await event.respond(get_text(uid, "សូមផ្ញើ ID ជនខិលខូចមកកាន់ទីនេះ៖", "Please send the Scammer's ID here:"))
        return

    elif text in ["📢 រាយការណ៍អ្នកបោក", "📢 Report Scammer"]:
        user_data[uid]['state'] = 'reporting_step1'
        await event.respond(get_text(uid, "សូមផ្ញើរូបភាពភស្តុតាង (Proof/KHQR):", "Please send the proof image/KHQR:"))
        return

    elif text in ["🌐 ប្តូរភាសា (Language)", "🌐 Change Language"]:
        buttons = [[Button.inline("Khmer 🇰🇭", b"set_kh"), Button.inline("English 🇺🇸", b"set_en")]]
        await event.respond("Select Language / ជ្រើសរើសភាសា", buttons=buttons)
        return

    # --- STATE HANDLING ---
    state = user_data[uid].get('state')

    if state == 'awaiting_id' and text.isdigit():
        user_id = int(text)
        try:
            async with user_client:
                full = await user_client(GetFullUserRequest(user_id))
                user = full.users[0]
                name = f"{user.first_name} {user.last_name or ''}"
                username = f"@{user.username}" if user.username else "N/A"
                res = get_text(uid, f"✅ ស្វែងរកឃើញ!\n👤 ឈ្មោះ: {name}\n🔗 User: {username}\n🆔 ID: {user_id}", 
                                    f"✅ Found!\n👤 Name: {name}\n🔗 User: {username}\n🆔 ID: {user_id}")
                await event.respond(res)
        except:
            await event.respond("❌ Not Found / រកមិនឃើញ")
        user_data[uid]['state'] = 'idle'

    elif state == 'reporting_step1' and event.photo:
        user_data[uid]['report_info']['photo'] = event.photo
        user_data[uid]['state'] = 'confirm_report'
        buttons = [[Button.inline("✅ YES", b"confirm_yes"), Button.inline("❌ NO", b"confirm_no")]]
        await event.respond(get_text(uid, "តើអ្នកប្រាកដថាចង់បញ្ជូនរបាយការណ៍នេះ?", "Are you sure you want to send this report?"), buttons=buttons)

    # --- OWNER COMMANDS ---
    if uid == OWNER_ID and text.startswith(".gent"):
        # Simple template generator
        parts = text.split()
        size = parts[1] if len(parts) > 1 else "small"
        template = (f"🚨 **NEW SCAMMER ALERT ({size.upper()})**\n"
                    "👤 Name: \n🆔 ID: \n💸 Amount: \n📢 Channel Subs: \n⚠️ Detail: ")
        await event.respond(template)

@bot.on(events.CallbackQuery)
async def callbacks(event):
    uid = event.sender_id
    data = event.data

    if data == b"set_kh":
        user_data[uid]['lang'] = 'kh'
        await event.edit("ភាសាត្រូវបានប្តូរទៅជា ខ្មែរ ✅", buttons=get_main_buttons(uid))
    elif data == b"set_en":
        user_data[uid]['lang'] = 'en'
        await event.edit("Language changed to English ✅", buttons=get_main_buttons(uid))
    
    elif data == b"confirm_yes":
        photo = user_data[uid]['report_info'].get('photo')
        # Send to Private Group
        await bot.send_message(PRIVATE_GROUP_ID, f"📢 **New Report from {uid}**", file=photo)
        await event.edit(get_text(uid, "របាយការណ៍ត្រូវបានបញ្ជូន! អរគុណ។", "Report sent! Thank you."))
        user_data[uid]['state'] = 'idle'
    
    elif data == b"confirm_no":
        user_data[uid]['state'] = 'idle'
        await event.edit(get_text(uid, "បានបោះបង់។", "Cancelled."), buttons=get_main_buttons(uid))

print("Vinzy Bot Started...")
bot.run_until_disconnected()
