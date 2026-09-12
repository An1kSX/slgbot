import json
import re
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Any

from slgbot.logger import logger
from slgbot.settings import Settings, get_settings
from slgbot.business_time import tashkent_time
from slgbot.log_archiving import daily_logs_path


def safe_chat_dir_name(chat_title: str) -> str:
	name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", chat_title)
	name = re.sub(r"\s+", "_", name)
	name = re.sub(r"_+", "_", name).strip(" ._")
	return name or "unknown_chat"


def html_path_builder(chat_id: int, moment: datetime, settings: Settings | None = None) -> Path:
	settings = settings or get_settings()
	file_path = daily_logs_path(settings.groups_dir, moment) / f"chat_{int(chat_id)}" / "chat_export"
	check_and_create_directory(file_path)
	return file_path


def check_and_create_directory(directory_path: Path) -> None:
	(directory_path / "css").mkdir(parents=True, exist_ok=True)
	(directory_path / "js").mkdir(parents=True, exist_ok=True)
	(directory_path / "img").mkdir(parents=True, exist_ok=True)
	(directory_path / "docs").mkdir(parents=True, exist_ok=True)


def create_html_file(
	chat_id: int,
	chat_name: str,
	file_path: Path,
	settings: Settings | None = None,
) -> None:
	settings = settings or get_settings()
	template_dir = Path(settings.html_template_dir)

	try:
		check_and_create_directory(file_path)
		copyfile(template_dir / "chat_export.html", file_path / "chat_export.html")
		copyfile(template_dir / "styles.css", file_path / "css" / "styles.css")
		copyfile(template_dir / "scripts.js", file_path / "js" / "scripts.js")
		copyfile(template_dir / "avatar.png", file_path / "img" / "avatar.png")
		copyfile(template_dir / "file.png", file_path / "img" / "file.png")

		html_file = file_path / "chat_export.html"
		html_content = html_file.read_text(encoding="utf-8")
		html_file.write_text(html_content.replace("ChatNaMe", chat_name), encoding="utf-8")

	except Exception as e:
		logger.error(f"Error creating HTML chat log for {chat_name} ({chat_id}): {e}")


def _sender_name(message: Any) -> str:
	user = getattr(message, "from_user", None)
	if user is not None:
		first_name = getattr(user, "first_name", "") or ""
		last_name = getattr(user, "last_name", "") or ""
		username = getattr(user, "username", "") or ""
		return f"{first_name} {last_name} (@{username})".strip()

	if getattr(message, "outgoing", False):
		return "Client through bot"

	return "Administrator"


def _write_js_call(file_path: Path, function_name: str, payload: dict[str, Any]) -> None:
	with (file_path / "js" / "scripts.js").open("a", encoding="utf-8") as file:
		file.write(f"{function_name}({json.dumps(payload, ensure_ascii=False)});\n")


def add_html_record(
	message: Any,
	is_img: bool | None = None,
	is_document: bool | None = None,
	img_path: str | None = None,
	document_path: str | None = None,
	document_name: str | None = None,
	settings: Settings | None = None,
) -> None:
	settings = settings or get_settings()
	file_path = html_path_builder(message.chat.id, message.date, settings)

	if not (file_path / "chat_export.html").exists():
		create_html_file(message.chat.id, message.chat.title, file_path, settings)

	try:
		base_payload = {
			"id": str(message.id),
			"sender": _sender_name(message),
			"time": tashkent_time(message.date).strftime("%d.%m.%Y %H:%M"),
			"avatarUrl": "img/avatar.png",
			"replyTo": str(getattr(message, "reply_to_message_id", None)),
		}

		if is_img:
			payload = {
				**base_payload,
				"imageUrl": img_path,
				"caption": getattr(message, "caption", None),
			}
			_write_js_call(file_path, "addImageMessage", payload)
			return

		if is_document:
			payload = {
				**base_payload,
				"fileName": document_name,
				"fileUrl": f"docs/{Path(document_path or '').name}",
				"iconUrl": "img/file.png",
				"caption": getattr(message, "caption", None),
			}
			_write_js_call(file_path, "addFileMessage", payload)
			return

		payload = {
			**base_payload,
			"text": getattr(message, "text", "") or "",
		}
		_write_js_call(file_path, "addMessage", payload)

	except Exception as e:
		logger.error(f"Error adding HTML chat record: {e}")
