import asyncio


def main() -> None:
	# Pyrogram needs an event loop before its client is imported.
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	from slgbot.bot import run

	run()


if __name__ == "__main__":
	main()
