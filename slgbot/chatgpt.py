from openai import AsyncOpenAI

from slgbot.logger import logger
from slgbot.settings import Settings, get_settings


SYSTEM_PROMPT = (
	"You classify Telegram messages for a legal services company. "
	"Answer only YES if the message is business-related: legal questions, "
	"requests for documents, consultations, deadlines, contracts, payments, "
	"appointments, or other client work. Answer only NO for greetings only, "
	"thanks only, jokes, spam, reactions, or non-business small talk."
)


async def is_business_message(text: str, settings: Settings | None = None) -> bool:
	settings = settings or get_settings()
	text = (text or "").strip()
	if not text:
		return False

	if not (settings.openai_api_key or "").strip():
		return False

	try:
		client = AsyncOpenAI(api_key=settings.openai_api_key)
		completion = await client.chat.completions.create(
			model=settings.openai_model,
			temperature=0,
			messages=[
				{"role": "system", "content": SYSTEM_PROMPT},
				{"role": "user", "content": text},
			],
		)
		answer = (completion.choices[0].message.content or "").strip().lower()
		return answer.startswith("yes") or answer.startswith("да")

	except Exception as e:
		logger.error(f"OpenAI business-message classification failed: {e}")
		return True
