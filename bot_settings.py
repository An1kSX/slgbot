from pyrogram import Client

from settings import get_settings


settings = get_settings()

bot = Client(
	settings.session_name,
	api_id=settings.api_id,
	api_hash=settings.api_hash,
	bot_token=settings.bot_token,
)
