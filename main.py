import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    print(f"✅ /start received from {message.from_user.id}")
    await message.reply_text("**✅ Bot is now working!**\n\nSend any Telegram post link to test.", quote=True)

@bot.on_message(filters.text & filters.private)
async def any_message(client, message: Message):
    print(f"✅ Message received: {message.text}")
    await message.reply_text("Message received! Bot is alive.", quote=True)

async def main():
    print("🚀 Starting bot...")
    await bot.start()
    print("✅ Bot started successfully!")
    await asyncio.Future()  # keep running

if __name__ == "__main__":
    asyncio.run(main())
