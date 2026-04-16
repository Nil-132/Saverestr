import os
import asyncio
import threading
import time
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserAlreadyParticipant, InviteHashExpired
from pyrogram.types import Message
from urllib.parse import urlparse, parse_qs

# FastAPI for keep-alive (required for Render free web service)
from fastapi import FastAPI
import uvicorn

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION = os.environ.get("SESSION", "")
AUTH = int(os.environ.get("AUTH", 0))
FORCESUB = os.environ.get("FORCESUB", "").strip("@")

PORT = int(os.environ.get("PORT", 10000))

bot = Client("savenileshya_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "✅ Save Restricted Bot is running (free tier with keep-alive)"}

cancel_batch = False

# Force Subscribe
async def force_sub(client: Client, message: Message) -> bool:
    if not FORCESUB:
        return True
    try:
        member = await client.get_chat_member(f"@{FORCESUB}", message.from_user.id)
        if member.status in ["left", "kicked"]:
            await message.reply_text(f"**Join @{FORCESUB} first to use the bot!**", quote=True)
            return False
    except:
        await message.reply_text(f"**Join @{FORCESUB} first!**", quote=True)
        return False
    return True

# Progress
def progress(current, total, msg: Message, status_type: str):
    try:
        percent = current * 100 / total
        asyncio.run_coroutine_threadsafe(
            msg.edit_text(f"__{status_type}__: **{percent:.1f}%**"), bot.loop
        )
    except:
        pass

# Parse Telegram link (supports topics)
def parse_link(link: str):
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

# Copy media (private needs download + re-upload)
async def copy_message(message: Message, chat_id, msg_id, thread_id=None, is_private=False):
    status = await message.reply_text("__Processing...__", quote=True)
    try:
        if is_private:
            msg = await user.get_messages(chat_id, msg_id)
            if msg.media:
                file = await user.download_media(
                    msg, progress=progress, progress_args=(status, "Downloading")
                )
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
                await bot.send_message(message.chat.id, msg.text, reply_to_message_id=message.id)
        else:
            msg = await bot.get_messages(chat_id, msg_id)
            await msg.copy(message.chat.id, reply_to_message_id=message.id)

        await status.edit_text("**✅ Saved successfully!**")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text(f"Waited {e.value} seconds due to flood...")
    except Exception as e:
        await status.edit_text(f"Error: {str(e)[:200]}")

# ===================== COMMANDS =====================
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if not await force_sub(client, message): return
    await message.reply_text(
        "**🚀 Combined Save Restricted Bot Ready!**\n\n"
        "• Send any public or private post link\n"
        "• For private: first send invite link\n"
        "• Supports Topics in groups\n"
        "Owner only: /batch /cancel /settings",
        quote=True
    )

@bot.on_message(filters.command("settings") & filters.private & filters.user(AUTH))
async def settings_cmd(client, message):
    await message.reply_text(
        f"**Settings**\nForce Subscribe: @{FORCESUB or 'Disabled'}\nOwner ID: {AUTH}",
        quote=True
    )

# Join private chat
@bot.on_message(filters.regex(r"https?://t\.me/(joinchat/|\+)") & filters.private)
async def join_chat(client, message):
    if not await force_sub(client, message): return
    try:
        await user.join_chat(message.text)
        await message.reply_text("**✅ Successfully joined the chat!**", quote=True)
    except UserAlreadyParticipant:
        await message.reply_text("**✅ Already a member.**", quote=True)
    except InviteHashExpired:
        await message.reply_text("**❌ Invite link expired.**", quote=True)
    except Exception as e:
        await message.reply_text(f"Error: {e}", quote=True)

# Main link handler
@bot.on_message(filters.text & filters.private)
async def handle_link(client, message):
    if not await force_sub(client, message): return
    text = message.text.strip()
    if not text.startswith("https://t.me/"): return

    chat_id, msg_id, thread_id, is_private = parse_link(text)
    if not chat_id or not msg_id:
        await message.reply_text("Invalid link!", quote=True)
        return
    await copy_message(message, chat_id, msg_id, thread_id, is_private)

# Batch command (owner only)
@bot.on_message(filters.command("batch") & filters.private & filters.user(AUTH))
async def batch_cmd(client, message):
    global cancel_batch
    if not await force_sub(client, message): return

    await message.reply_text("**Send first post link**", quote=True)
    start_msg = await client.listen(message.chat.id, filters.text, timeout=300)
    await message.reply_text("**Send last post link**", quote=True)
    end_msg = await client.listen(message.chat.id, filters.text, timeout=300)

    try:
        start_chat, start_id, _, _ = parse_link(start_msg.text)
        _, end_id, _, _ = parse_link(end_msg.text)
        if start_chat != end_chat:
            await message.reply_text("Both links must be from the same chat!", quote=True)
            return
    except:
        await message.reply_text("Invalid links!", quote=True)
        return

    cancel_batch = False
    status = await message.reply_text("**Batch started...**", quote=True)

    for i in range(start_id, end_id + 1):
        if cancel_batch:
            await status.edit_text("**Batch cancelled!**")
            return
        try:
            await copy_message(message, start_chat, i, is_private=True)
            await asyncio.sleep(3)  # Anti-flood
        except:
            continue

    await status.edit_text("**✅ Batch completed!**")

@bot.on_message(filters.command("cancel") & filters.private & filters.user(AUTH))
async def cancel_cmd(client, message):
    global cancel_batch
    cancel_batch = True
    await message.reply_text("**Stopping batch soon...**", quote=True)

# ===================== RUN BOT =====================
async def run_bot():
    await user.start()
    print("✅ User account (for private channels) started")
    await bot.start()
    print("✅ Bot started successfully!")
    await asyncio.Future()  # Keep bot running

async def main():
    # Run bot and web server together
    bot_task = asyncio.create_task(run_bot())
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(bot_task, server.serve())

if __name__ == "__main__":
    print("Starting combined bot on Render free tier...")
    asyncio.run(main())
