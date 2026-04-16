import os
import asyncio
import time
import threading
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, FloodWait, MessageNotModified
from pyrogram.types import Message
from urllib.parse import urlparse, parse_qs

# === CONFIG FROM RENDER ENVIRONMENT VARIABLES ===
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION = os.environ.get("SESSION", "")
AUTH = int(os.environ.get("AUTH", 0))
FORCESUB = os.environ.get("FORCESUB", "").strip("@")

bot = Client("savenileshya_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

cancel_batch = False

async def force_sub(client, message):
    if not FORCESUB:
        return True
    try:
        member = await client.get_chat_member(f"@{FORCESUB}", message.from_user.id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(f"**Join @{FORCESUB} first!**", quote=True)
            return False
    except:
        await message.reply_text(f"**Join @{FORCESUB} first!**", quote=True)
        return False
    return True

def progress(current, total, msg, status_type):
    try:
        percent = current * 100 / total
        asyncio.run_coroutine_threadsafe(msg.edit_text(f"__{status_type}__: **{percent:.1f}%**"), bot.loop)
    except:
        pass

def parse_link(link):
    parsed = urlparse(link)
    path = parsed.path.strip("/").split("/")
    query = parse_qs(parsed.query)
    thread_id = int(query.get("thread", [0])[0]) or None

    if "t.me/c/" in link:
        chat_id = int("-100" + path[-2])
        msg_id = int(path[-1])
        is_private = True
    else:
        chat_id = path[-2]
        msg_id = int(path[-1])
        is_private = False
    return chat_id, msg_id, thread_id, is_private

async def copy_message(message: Message, chat_id, msg_id, thread_id=None, is_private=False):
    status = await message.reply_text("__Processing...__", quote=True)
    try:
        if is_private:
            msg = await user.get_messages(chat_id, msg_id)
            if msg.media:
                file = await user.download_media(msg, progress=progress, progress_args=(status, "Downloading"))
                # Send media with proper type
                if msg.document:
                    await bot.send_document(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
                elif msg.video:
                    await bot.send_video(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
                elif msg.photo:
                    await bot.send_photo(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
                else:
                    await bot.send_message(message.chat.id, msg.text or "Media saved", reply_to_message_id=message.id)
                if os.path.exists(file):
                    os.remove(file)
        else:
            msg = await bot.get_messages(chat_id, msg_id)
            await msg.copy(message.chat.id, reply_to_message_id=message.id)
        await status.edit_text("**✅ Saved successfully!**")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text(f"Waited {e.value} seconds...")
    except Exception as e:
        await status.edit_text(f"Error: {str(e)[:150]}")

# ====================== COMMANDS ======================
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await force_sub(client, message): return
    await message.reply_text("**✅ Combined Save Bot Ready!**\nSend any post link.\nSupports Topics & Private channels.\nOwner commands: /batch /settings", quote=True)

@bot.on_message(filters.command("settings") & filters.private & filters.user(AUTH))
async def settings(client, message):
    await message.reply_text(f"**Settings**\nForceSub: @{FORCESUB or 'Disabled'}\nOwner: {AUTH}", quote=True)

@bot.on_message(filters.regex(r"https?://t\.me/") & filters.private)
async def handle_link(client, message):
    if not await force_sub(client, message): return
    text = message.text.strip()
    chat_id, msg_id, thread_id, is_private = parse_link(text)
    await copy_message(message, chat_id, msg_id, thread_id, is_private)

@bot.on_message(filters.command("batch") & filters.private & filters.user(AUTH))
async def batch(client, message):
    global cancel_batch
    if not await force_sub(client, message): return
    await message.reply_text("Send first link", quote=True)
    s = await client.listen(message.chat.id, timeout=300)
    await message.reply_text("Send last link", quote=True)
    e = await client.listen(message.chat.id, timeout=300)
    try:
        start_chat, start_id, _, _ = parse_link(s.text)
        _, end_id, _, _ = parse_link(e.text)
        cancel_batch = False
        st = await message.reply_text("Batch started...", quote=True)
        for i in range(start_id, end_id+1):
            if cancel_batch: break
            await copy_message(message, start_chat, i, is_private=True)
            await asyncio.sleep(3)
        await st.edit_text("✅ Batch done!")
    except:
        await message.reply_text("Invalid links", quote=True)

@bot.on_message(filters.command("cancel") & filters.private & filters.user(AUTH))
async def cancel(client, message):
    global cancel_batch
    cancel_batch = True
    await message.reply_text("Batch stopping...", quote=True)

async def main():
    await user.start()
    await bot.start()
    print("Bot is running 24/7 with combined features!")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
