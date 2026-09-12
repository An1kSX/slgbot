from datetime import datetime
from typing import Any

from slgbot.settings import Settings
from slgbot.business_time import tashkent_time


def _value(value: Any) -> str:
	return "" if value is None else str(value)


def message_text(message: Any) -> str:
	return _value(getattr(message, "text", None) or getattr(message, "caption", None)).strip()


def _contains_marker(value: str, settings: Settings) -> bool:
	marker = settings.staff_marker.lower()
	return bool(marker and marker in value.lower())


def is_client_user(user: Any, chat_member_title: str | None, settings: Settings) -> bool:
	if user is None:
		return False

	user_id = getattr(user, "id", None)
	username = _value(getattr(user, "username", "")).lower().lstrip("@")
	full_name = " ".join(
		part for part in [
			_value(getattr(user, "first_name", "")),
			_value(getattr(user, "last_name", "")),
		]
		if part
	)

	if user_id in settings.staff_user_ids:
		return False
	if username and username in settings.staff_usernames:
		return False
	if _contains_marker(full_name, settings):
		return False
	if _contains_marker(username, settings):
		return False
	if chat_member_title and _contains_marker(chat_member_title, settings):
		return False

	return True


def is_working_time(moment: datetime, settings: Settings) -> bool:
	# Naive values passed directly to this schedule helper are business wall time.
	if moment.tzinfo is not None:
		moment = tashkent_time(moment)
	if moment.weekday() not in settings.working_days:
		return False
	current_time = moment.time()
	return settings.work_start <= current_time < settings.work_end


def should_handle_appeal(
	message: Any,
	*,
	chat_member_title: str | None,
	settings: Settings,
	is_business_message: bool,
	has_active_cooldown: bool,
) -> bool:
	if getattr(message, "outgoing", False):
		return False
	if not message_text(message):
		return False
	if has_active_cooldown:
		return False
	if is_working_time(tashkent_time(getattr(message, "date")), settings):
		return False
	if not is_client_user(getattr(message, "from_user", None), chat_member_title, settings):
		return False
	return is_business_message
