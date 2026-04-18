import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn

print("=== BOT STARTING ===")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION = os.getenv("SESSION")
PORT = int(os.getenv("PORT", 10000))

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User client is now optional
user = None
if SESSION:
    user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
    print("SESSION found - User client will be started")
else:
    print("No SESSION - Private channels will not work (bot will still work for public links)")

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is alive"}

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    print(f"DEBUG: /start received from {message.from_user.id}")
    await message.reply_text("**✅ Bot is now working!**\nSend any Telegram post link to test.", quote=True)

@bot.on_message(filters.text & filters.private)
async def handle_link(client, message: Message):
    print(f"DEBUG: Message received: {message.text}")
    if "t.me/" in message.text:
        await message.reply_text("Link received! (Processing...)", quote=True)
    else:
        await message.reply_text("Please send a Telegram post link", quote=True)

async def run_bot():
    if user:
        print("Starting user client...")
        try:
            await user.start()
            print("✅ User client started")
        except Exception as e:
            print(f"User client error: {e}")
    else:
        print("Skipping user client (no SESSION)")

    print("Starting bot client...")
    await bot.start()
    print("✅ Bot started successfully on free tier!")
    await asyncio.Future()

async def main():
    print("Starting main()...")
    bot_task = asyncio.create_task(run_bot())
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT)
    server = uvicorn.Server(config)
    await asyncio.gather(bot_task, server.serve(), return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
