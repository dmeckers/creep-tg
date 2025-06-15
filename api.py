from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["messages"])

# This will be set during startup
telegram_app = None


@router.post("/send-message")
async def send_message(request: Request) -> Dict[str, Any]:
    data = await request.json()
    chat_id = data.get("chat_id")
    message = data.get("message")

    print(f"Received request to send message: {data}")

    if not chat_id or not message:
        return {"error": "Missing chat_id or message", "status": 400}

    try:
        # Access the bot through the application instance
        bot = telegram_app.bot
        await bot.send_message(chat_id=chat_id, text=message)
        return {"status": "sent", "code": 200}
    except Exception as e:
        return {"error": str(e), "status": 500}
