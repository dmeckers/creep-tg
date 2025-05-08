import asyncio
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    Application,
)

API_TOKEN = "7504051741:AAEjNmzUp7_g53OsWmb8YwED4ijBKH0IzIU"

web_app_url = "https://creamradio.netlify.app/"

app = FastAPI()
bot = Bot(token=API_TOKEN)

telegram_app: Application = ApplicationBuilder().token(API_TOKEN).build()

# ====== TG Handlers ======


async def defaultGreetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Open Web App", web_app=WebAppInfo(web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # await update.message.reply_text(
    #     "Welcome to Cream Radio! Hit the button below to open the radio.",
    #     reply_markup=reply_markup,
    # )
    user_chat = update.message.chat
    await update.message.reply_text(
        f"Welcome to Cream Radio {update.message.from_user.id} ! Hit the button below to open the radio. Chat ID: {user_chat.id}, Chat Type: {user_chat.type}, User ID: {user_chat.username or user_chat.id}",
        reply_markup=reply_markup,
    )


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await defaultGreetings(update, context)


telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler)
)

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

# use Illuminate\Support\Facades\Http;
# $response = Http::post('http://tg:3000/send-message' , ['chat_id' => 12345 , 'text' => 'Test!']);
# https://chatgpt.com/c/681b983c-02d8-8003-b9ef-8428658cfd41
