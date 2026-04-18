import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, PeerIdInvalid
from pyrogram.types import Message
from urllib.parse import urlparse, parse_qs
from fastapi import FastAPI
import uvicorn

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION = os.getenv("SESSION")
AUTH = int(os.getenv("AUTH", 0))
FORCESUB = os.getenv("FORCESUB", "").strip("@")
PORT = int(os.getenv("PORT", 10000))

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION) if SESSION else None

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "✅ Bot is running on Render free tier"}

async def force_sub(message: Message):
    if not FORCESUB:
        return True
    try:
        member = await bot.get_chat_member(f"@{FORCESUB}", message.from_user.id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(f"**Join @{FORCESUB} first!**", quote=True)
            return False
    except:
        await message.reply_text(f"**Join @{FORCESUB} first!**", quote=True)
        return False
    return True

def parse_link(link: str):
    parsed = urlparse(link)
    path = parsed.path.strip("/").split("/")
    if "t.me/c/" in link:
        chat_id = int("-100" + path[-2])
        msg_id = int(path[-1])
        is_private = True
    else:
        chat_id = path[-2]
        msg_id = int(path[-1])
        is_private = False
    return chat_id, msg_id, is_private

async def copy_message(message: Message, chat_id, msg_id, is_private=False):
    status = await message.reply_text("__Processing...__", quote=True)
    try:
        if is_private and user:
            msg = await user.get_messages(chat_id, msg_id)
        else:
            msg = await bot.get_messages(chat_id, msg_id)

        if msg.media and is_private and user:
            file = await user.download_media(msg)
            if msg.document:
                await bot.send_document(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
            elif msg.video:
                await bot.send_video(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
            elif msg.photo:
                await bot.send_photo(message.chat.id, file, caption=msg.caption, reply_to_message_id=message.id)
            else:
                await bot.send_message(message.chat.id, msg.text or "Saved", reply_to_message_id=message.id)
            if os.path.exists(file): os.remove(file)
        else:
            await msg.copy(message.chat.id, reply_to_message_id=message.id)
        await status.edit_text("**✅ Saved!**")
    except PeerIdInvalid:
        await status.edit_text("**❌ Send invite link first for private channels.**")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text(f"Waited {e.value}s")
    except Exception as e:
        await status.edit_text(f"Error: {str(e)[:100]}")

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if not await force_sub(message): return
    await message.reply_text("**✅ Save Restricted Bot is Online!**\nSend any post link to save it.", quote=True)

@bot.on_message(filters.text & filters.private)
async def handle_link(client, message):
    if not await force_sub(message): return
    text = message.text.strip()
    if not text.startswith("https://t.me/"): return
    chat_id, msg_id, is_private = parse_link(text)
    await copy_message(message, chat_id, msg_id, is_private)

async def run_bot():
    if user:
        await user.start()
        print("✅ User client started")
    await bot.start()
    print("✅ Bot started successfully on free tier!")
    await asyncio.Future()

async def main():
    bot_task = asyncio.create_task(run_bot())
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT)
    server = uvicorn.Server(config)
    await asyncio.gather(bot_task, server.serve(), return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
