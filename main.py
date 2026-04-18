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
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION) if SESSION else None

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is alive"}

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    print(f"DEBUG: Received /start from {message.from_user.id}")
    await message.reply_text("**✅ Bot is working!**\nSend any post link to test.", quote=True)

@bot.on_message(filters.text & filters.private)
async def handle_link(client, message: Message):
    print(f"DEBUG: Received message: {message.text}")
    if message.text.startswith("https://t.me/"):
        print("DEBUG: Detected Telegram link")
        await message.reply_text("Link received! Processing...", quote=True)
    else:
        await message.reply_text("Send a Telegram post link", quote=True)

async def run_bot():
    print("Starting user client...")
    if user:
        await user.start()
        print("✅ User client started")
    print("Starting bot client...")
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
