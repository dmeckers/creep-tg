from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn
import aiohttp
import io

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    Application,
)
import os

# TODO::Separate all stuff
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_APP_URL = os.environ.get("WEB_APP_URL")
API_URL = os.environ.get("API_URL")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)

telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# ====== TG Handlers ======


async def defaultGreetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Open Web App", web_app=WebAppInfo(WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_chat = update.message.chat
    await update.message.reply_text(
        f"Welcome to Cream Radio {update.message.from_user.id} ! Hit the button below to open the radio. Chat ID: {user_chat.id}, Chat Type: {user_chat.type}, User ID: {user_chat.username or user_chat.id}",
        reply_markup=reply_markup,
    )


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await defaultGreetings(update, context)


async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await defaultGreetings(update, context)


async def audio_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio

    if not audio:
        await update.message.reply_text("Please send an audio file.")
        return

    file_id = audio.file_id
    file = await context.bot.get_file(file_id)
    file_url = file.file_path

    print(f"Received audio file: {file_id}, URL: {file_url}")

    # post to api
    response = await send_audio_to_api(file_url, file_id)

    if response.get("code") == 200 or response.get("code") == 201:
        await update.message.reply_text(
            f"Audio file {file_id} successfully sent to the API."
        )
    else:
        await update.message.reply_text(
            f"Failed to send audio file {file_id} to the API. Error: {response.get('error', 'Unknown error')}"
        )


async def send_audio_to_api(file_url: str, file_id: str):
    """Send the audio file to your internal API"""
    # Define your API endpoint - use service name as hostname

    upload_audio_url = f"{API_URL}/api/v1/songs"

    async with aiohttp.ClientSession() as session:
            async with session.post(
                upload_audio_url, data={
                    "file_url": file_url,
                    "file_id": file_id,
                }
            ) as api_response:
                return await api_response.json()


telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler)
)

telegram_app.add_handler(MessageHandler(filters.COMMAND, start_command_handler))
telegram_app.add_handler(MessageHandler(filters.AUDIO, audio_message_handler))


# ====== Lifespan Events ======


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Telegram bot...")
    await telegram_app.initialize()
    await telegram_app.start()
    telegram_app.create_task(telegram_app.updater.start_polling())
    yield
    print("Shutting down Telegram bot...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app.router.lifespan_context = lifespan

# ====== FastAPI Endpoint ======


@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    chat_id = data.get("chat_id")
    message = data.get("message")

    print(f"Received request to send message: {data} ")

    if chat_id and message:
        await bot.send_message(chat_id=chat_id, text=message)
        return {"status": "sent"}
    return {"error": "Missing chat_id or message"}


# ====== Run ======

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
