import asyncio
import os
from telethon import TelegramClient, events, Button
import aiohttp
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_UPLOAD_URL = f"{os.environ.get('API_URL', 'http://api')}/api/upload-from-bot"
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://mini-app.example.com")

print(f"Using API URL: {API_UPLOAD_URL}")

client = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def send_audio_to_api(file_path: str, file_id: str, user, filename: str):
    timeout = aiohttp.ClientTimeout(total=600)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("file_id", file_id)
                form.add_field("telegram_user_id", str(user.id))
                form.add_field("telegram_user_first_name", user.first_name or "")
                form.add_field("telegram_user_username", user.username or "")
                form.add_field("filename", filename)
                form.add_field("file", f, filename=filename, content_type="audio/mpeg")
                async with session.post(
                    API_UPLOAD_URL, data=form, headers={"Accept": "application/json"}
                ) as resp:
                    if resp.content_type == "application/json":
                        return await resp.json()
                    else:
                        text = await resp.text()
                        return {
                            "code": resp.status,
                            "error": f"Unexpected response: {text[:100]}...",
                            "content_type": resp.content_type,
                        }
    except Exception as e:
        return {"code": 500, "error": f"Request failed: {str(e)}"}


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    keyboard = [[Button.url("Open Mini App", url=WEB_APP_URL)]]

    await event.reply("Click the button below to open our Mini App:", buttons=keyboard)


@client.on(events.NewMessage)
async def handler(event):
    if event.message.audio:
        audio = event.message.audio
        filename = get_audio_filename(audio)
        file_path = f"/tmp/{filename}"

        file_size_mb = audio.size / 1024 / 1024

        if file_size_mb > 30:
            await event.reply(
                f"⚠️ File size is {file_size_mb:.2f}MB — upload may take a while..."
            )

        await client.download_media(audio, file=file_path)

        response = await send_audio_to_api(
            file_path, str(audio.id), event.message.sender, filename
        )

        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete temp file: {e}")

        if response.get("data"):
            await event.reply("Song uploaded successfully.")
        elif response.get("exception") == "App\\Exceptions\\SongAlreadyAddedException":
            await event.reply(
                "Song has already been added. You can find it in the library."
            )
        else:
            await event.reply("Failed to save song.")
    else:
        keyboard = [[Button.url("Open Mini App", url=WEB_APP_URL)]]

        await event.reply(
            "Click the button below to open our Mini App:", buttons=keyboard
        )


def get_audio_filename(audio):
    for attr in audio.attributes:
        if isinstance(attr, DocumentAttributeFilename):
            return attr.file_name
    return f"{audio.id}.mp3"


if __name__ == "__main__":
    print("Starting Telethon bot...")
    client.run_until_disconnected()
