import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn

print("1. Starting script...")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION = os.getenv("SESSION")
AUTH = int(os.getenv("AUTH", 0))
FORCESUB = os.getenv("FORCESUB", "").strip("@")
PORT = int(os.getenv("PORT", 10000))

print("2. Config loaded")

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION) if SESSION else None

print("3. Clients created")

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is running"}

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text("**✅ Bot is working!**\nSend any post link to test.", quote=True)

async def run_bot():
    print("4. Starting user client...")
    if user:
        await user.start()
        print("✅ User client started")
    print("5. Starting bot client...")
    await bot.start()
    print("✅ Bot started successfully on free tier!")
    await asyncio.Future()

async def main():
    print("6. Starting main()...")
    bot_task = asyncio.create_task(run_bot())
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT)
    server = uvicorn.Server(config)
    await asyncio.gather(bot_task, server.serve(), return_exceptions=True)

if __name__ == "__main__":
    print("7. Running asyncio...")
    asyncio.run(main())
