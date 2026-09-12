from datetime import datetime
from zoneinfo import ZoneInfo


BUSINESS_TIMEZONE = ZoneInfo("Asia/Tashkent")


def tashkent_time(moment: datetime) -> datetime:
	# Pyrogram 2.0.106 returns naive datetimes in the host's local timezone.
	return moment.astimezone(BUSINESS_TIMEZONE)


def business_now() -> datetime:
	return datetime.now(BUSINESS_TIMEZONE)
