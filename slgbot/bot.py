import asyncio
import json
import zipfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from pyrogram import filters, utils
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup

from slgbot import chatgpt
from slgbot import db_functions as db
from slgbot.admin_state import AdminStateStore
from slgbot.appeals import is_client_user, message_text, should_handle_appeal
from slgbot.bot_settings import bot
from slgbot.chat_to_html import add_html_record, html_path_builder, safe_chat_dir_name
from slgbot.log_archiving import archive_group_logs, daily_logs_path, log_date_label
from slgbot.business_time import business_now, tashkent_time
from slgbot.logger import logger
from slgbot.runtime_settings import load_runtime_settings, toggle_new_group_notifications
from slgbot.settings import get_settings


settings = get_settings()
admin_states = AdminStateStore(
	settings.admin_ids | settings.superadmin_ids,
	db.get_state,
	db.set_state,
)

MENU_BUTTONS = [
	[KeyboardButton("Список чатов")],
	[KeyboardButton("Выгрузить чаты"), KeyboardButton("Удалить бота из чата")],
	[KeyboardButton("Уведомления о новых группах")],
]


def get_peer_type_new(peer_id: int) -> str:
	peer_id_str = str(peer_id)
	if not peer_id_str.startswith("-"):
		return "user"
	if peer_id_str.startswith("-100"):
		return "channel"
	return "chat"


utils.get_peer_type = get_peer_type_new


def chat_title(message: Any) -> str:
	return message.chat.title or str(message.chat.id)


def chat_dir(message: Any) -> Path:
	return html_path_builder(message.chat.id, message.date, settings).parent


def json_log_path(message: Any) -> Path:
	return chat_dir(message) / "data.json"


def add_record_to_json_file(file_path: Path, new_record: dict[str, Any]) -> None:
	data = []
	if file_path.exists():
		try:
			data = json.loads(file_path.read_text(encoding="utf-8"))
		except json.JSONDecodeError:
			data = []

	data.append(new_record)
	file_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")


async def db_admin_ids() -> set[int]:
	try:
		return {int(admin[1]) for admin in await db.get_admins()}
	except Exception as e:
		logger.error(f"Error loading admins from database: {e}")
		return set()


async def db_superadmin_ids() -> set[int]:
	try:
		return {int(admin[1]) for admin in await db.get_super_admins()}
	except Exception as e:
		logger.error(f"Error loading superadmins from database: {e}")
		return set()


async def admin_recipients() -> set[int]:
	return set(settings.admin_ids) | set(settings.superadmin_ids) | await db_admin_ids()


async def is_admin_user(user_id: int) -> bool:
	return settings.is_admin_id(user_id) or user_id in await db_admin_ids()


async def is_superadmin_user(user_id: int) -> bool:
	return settings.is_superadmin_id(user_id) or user_id in await db_superadmin_ids()


async def superadmin_recipients() -> set[int]:
	return set(settings.superadmin_ids) | await db_superadmin_ids()


async def bootstrap_database_records() -> None:
	try:
		await db.bootstrap_admins(settings.admin_ids, settings.superadmin_ids)
	except Exception as e:
		logger.error(f"Error bootstrapping admins: {e}")


async def notify_new_group(message: Any) -> None:
	runtime = load_runtime_settings(settings.runtime_settings_file)
	if not runtime.new_group_notifications_enabled:
		return

	text = (
		"Бот добавлен в новую группу.\n"
		f"Название: {chat_title(message)}\n"
		f"ID: {message.chat.id}"
	)
	for recipient in await admin_recipients():
		try:
			await bot.send_message(chat_id=int(recipient), text=text)
		except Exception as e:
			logger.error(f"Error notifying admin {recipient} about new group {message.chat.id}: {e}")


async def build_group_markup(groups: list[tuple[str, int]], page: int = 0) -> InlineKeyboardMarkup:
	per_page = 20
	total_pages = max(1, (len(groups) + per_page - 1) // per_page)
	start = page * per_page
	end = start + per_page

	keyboard = [
		[InlineKeyboardButton(name, callback_data=str(group_id))]
		for name, group_id in groups[start:end]
	]

	nav_row: list[InlineKeyboardButton] = []
	if page > 0:
		nav_row.append(InlineKeyboardButton("Назад", callback_data=f"page_{page - 1}"))

	nav_row.append(InlineKeyboardButton("Скрыть список", callback_data="rem"))

	if page < total_pages - 1:
		nav_row.append(InlineKeyboardButton("Вперед", callback_data=f"page_{page + 1}"))

	keyboard.append(nav_row)
	return InlineKeyboardMarkup(keyboard)


async def ensure_group_registered(message: Any) -> None:
	await db.add_group(message.chat.id, chat_title(message))


async def chat_member_title(message: Any) -> str | None:
	user = getattr(message, "from_user", None)
	if user is None:
		return None

	try:
		member = await bot.get_chat_member(message.chat.id, user.id)
	except Exception as e:
		logger.warning(f"Could not load chat member {user.id} in {message.chat.id}: {e}")
		return None

	title = getattr(member, "custom_title", None)
	if title:
		return title

	status = str(getattr(member, "status", ""))
	if status in {"ChatMemberStatus.OWNER", "ChatMemberStatus.ADMINISTRATOR", "OWNER", "ADMINISTRATOR"}:
		return "Administrator"

	return None


async def user_info_parser(message: Any, member_title: str | None = None) -> tuple[str, str]:
	user = getattr(message, "from_user", None)
	if user is None:
		return ("Client", "Client through bot") if getattr(message, "outgoing", False) else ("Administrator", "Administrator")

	name = f"{user.first_name or ''} {user.last_name or ''}".strip()
	username = f"@{user.username}" if user.username else ""
	display = " ".join(part for part in [name, username, f"(id:{user.id})"] if part)
	role = "Client" if is_client_user(user, member_title, settings) else "Staff"
	return role, display


async def log_text_message(message: Any, member_title: str | None = None) -> None:
	title = chat_title(message)
	role, user = await user_info_parser(message, member_title)
	record = {
		"chat_id": message.chat.id,
		"chat_title": title,
		"user": f"{user} ({role})",
		"message_id": message.id,
		"message_reply_to_message_id": message.reply_to_message_id,
		"text": message.text,
		"timestamp": tashkent_time(message.date).strftime("%H:%M:%S"),
	}
	add_record_to_json_file(json_log_path(message), record)
	add_html_record(message, settings=settings)


async def log_document_message(message: Any, member_title: str | None = None) -> None:
	title = chat_title(message)
	role, user = await user_info_parser(message, member_title)
	document_name = message.document.file_name
	record = {
		"chat_id": message.chat.id,
		"chat_title": title,
		"user": f"{user} ({role})",
		"message_id": message.id,
		"message_reply_to_message_id": message.reply_to_message_id,
		"document": document_name,
		"caption": message.caption,
		"timestamp": tashkent_time(message.date).strftime("%H:%M:%S"),
	}

	file_size_mb = message.document.file_size / (1024 * 1024)
	if file_size_mb <= settings.max_document_mb:
		export_path = html_path_builder(message.chat.id, message.date, settings)
		file_name = safe_chat_dir_name(f"{message.document.file_unique_id}_{document_name}")
		document_path = export_path / "docs" / file_name
		if not document_path.exists():
			await bot.download_media(message=message, file_name=str(document_path))
		add_html_record(
			message,
			is_document=True,
			document_path=str(document_path),
			document_name=document_name,
			settings=settings,
		)

	add_record_to_json_file(json_log_path(message), record)


async def log_photo_message(message: Any, member_title: str | None = None) -> None:
	title = chat_title(message)
	role, user = await user_info_parser(message, member_title)
	record = {
		"chat_id": message.chat.id,
		"chat_title": title,
		"user": f"{user} ({role})",
		"message_id": message.id,
		"message_reply_to_message_id": message.reply_to_message_id,
		"photo": "(image)",
		"caption": message.caption,
		"timestamp": tashkent_time(message.date).strftime("%H:%M:%S"),
	}

	export_path = html_path_builder(message.chat.id, message.date, settings)
	image_name = f"photo-{message.photo.file_unique_id}.png"
	image_path = export_path / "img" / image_name
	if not image_path.exists():
		await bot.download_media(message=message, file_name=str(image_path))
	add_html_record(message, is_img=True, img_path=f"img/{image_name}", settings=settings)

	add_record_to_json_file(json_log_path(message), record)


async def handle_appeal(message: Any, member_title: str | None) -> None:
	if not settings.openai_api_key:
		return

	text = message_text(message)
	if not text:
		return

	has_active_cooldown = await db.group_has_active_cooldown(message.chat.id)
	if not should_handle_appeal(
		message,
		chat_member_title=member_title,
		settings=settings,
		is_business_message=True,
		has_active_cooldown=has_active_cooldown,
	):
		return

	is_business = await chatgpt.is_business_message(text, settings)
	if not should_handle_appeal(
		message,
		chat_member_title=member_title,
		settings=settings,
		is_business_message=is_business,
		has_active_cooldown=has_active_cooldown,
	):
		return

	await db.group_change_appeal(message.chat.id, True)
	await db.set_group_cooldown(message.chat.id, settings.appeal_cooldown_seconds)
	await message.reply(settings.appeal_auto_reply)


def count_folders(directory: Path) -> int:
	if not directory.exists():
		return 0
	return sum(item.is_dir() for item in directory.iterdir())


def zip_directory(source_path: Path, zip_path: Path) -> bool:
	try:
		source_path.mkdir(parents=True, exist_ok=True)
		chat_list = sorted(item.name for item in source_path.iterdir() if item.is_dir())
		chats_file = source_path / "chats.txt"
		chats_file.write_text(
			"Exported chats:\n" + "\n".join(chat_list),
			encoding="utf-8",
		)

		with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
			for item in source_path.rglob("*"):
				if item.is_file():
					zip_file.write(item, item.relative_to(source_path.parent))

		chats_file.unlink(missing_ok=True)
		return True

	except Exception as e:
		logger.error(f"Error zipping chat logs: {e}")
		return False


async def chats_download(chat_id: int | None = None) -> None:
	now = business_now()
	groups_path = daily_logs_path(settings.groups_dir, now)
	log_label = log_date_label(now)
	zip_path = Path(f"{settings.log_zip_prefix}_{log_label}_{now.strftime('%H%M%S')}.zip")
	if not zip_directory(groups_path, zip_path):
		return

	caption = (
		f"Выгрузка чатов за {log_label}\n"
		f"Количество чатов: {count_folders(groups_path)}"
	)
	recipients = {chat_id} if chat_id is not None else await superadmin_recipients()

	try:
		for recipient in recipients:
			await bot.send_document(chat_id=int(recipient), document=str(zip_path), caption=caption)
	finally:
		zip_path.unlink(missing_ok=True)


async def send_grouplist_with_appeals() -> None:
	if not settings.openai_api_key:
		return

	try:
		groups = await db.groups_with_appeal()
		recipients = await superadmin_recipients()
		if not recipients:
			logger.warning("No superadmin recipients configured for appeal report")
			return

		if not groups:
			text = "За нерабочее время обращений от клиентов зафиксировано не было."
		else:
			group_list = "\n".join(f"- {group[0]}" for group in groups)
			text = f"Чаты, где в нерабочее время были обращения:\n{group_list}"

		for recipient in recipients:
			await bot.send_message(chat_id=int(recipient), text=text)

		if groups:
			await db.groups_clear_appeal_by_ids([int(group[1]) for group in groups])

	except Exception as e:
		logger.error(f"Error sending appeal group list: {e}")


async def archive_current_logs() -> None:
	try:
		archived_count = archive_group_logs(
			settings.groups_dir,
			settings.log_archive_dir,
			business_now(),
		)
		logger.info(f"Archived {archived_count} group log folders")
	except Exception as e:
		logger.error(f"Error archiving group logs: {e}")


async def run_daily_scheduler() -> None:
	logger.info("Daily scheduler started")
	last_appeal_report_date: str | None = None
	last_archive_date: str | None = None
	while True:
		now = business_now()
		today = now.strftime("%Y-%m-%d")
		if now.strftime("%H:%M") == settings.appeal_report_time and last_appeal_report_date != today:
			await send_grouplist_with_appeals()
			last_appeal_report_date = today
		if now.strftime("%H:%M") == settings.log_archive_time and last_archive_date != today:
			await archive_current_logs()
			last_archive_date = today
		await asyncio.sleep(30)


@bot.on_message(filters.command("start") & filters.private & filters.incoming)
async def start(_, message):
	if not await is_admin_user(message.chat.id):
		return

	await admin_states.set(message.chat.id, "menu")
	await bot.send_message(
		chat_id=message.chat.id,
		text="Главное меню",
		reply_markup=ReplyKeyboardMarkup(MENU_BUTTONS, resize_keyboard=True),
	)


@bot.on_message(filters.new_chat_title & filters.group)
async def update_title(_, message):
	await db.update_group_title(message.chat.id, chat_title(message))


@bot.on_message(filters.left_chat_member & filters.group)
async def chat_left(_, message):
	if settings.bot_user_id and message.left_chat_member.id == settings.bot_user_id:
		logger.info(f"Bot left chat {chat_title(message)}")
		await db.remove_group(message.chat.id)


@bot.on_message(filters.new_chat_members & filters.group)
async def new_group_checking(_, message):
	new_members = message.new_chat_members or []
	bot_added = any(
		(settings.bot_user_id and member.id == settings.bot_user_id)
		or (settings.bot_username and (member.username or "").lower() == settings.bot_username.lower().lstrip("@"))
		for member in new_members
	)
	if not bot_added:
		return

	if not await db.add_group(message.chat.id, chat_title(message)):
		await bot.send_message(
			chat_id=message.chat.id,
			text="Не удалось добавить чат в список. Попробуйте добавить бота позже.",
		)
		return

	await notify_new_group(message)


@bot.on_message(filters.private & filters.text & filters.incoming)
async def admin(_, message):
	if not await is_admin_user(message.chat.id):
		return

	state = await admin_states.get(message.chat.id)

	if message.text == "Список чатов":
		groups = await db.get_groups()
		lines = [f"{index}) {group[0]}" for index, group in enumerate(groups, start=1)]
		if not lines:
			await bot.send_message(chat_id=message.chat.id, text="Список чатов пуст.")
			return

		for start_index in range(0, len(lines), 50):
			chunk = lines[start_index:start_index + 50]
			if start_index + 50 >= len(lines):
				chunk.append(f"Всего групп: {len(lines)}")
			await bot.send_message(chat_id=message.chat.id, text="\n".join(chunk))
		return

	if message.text == "Выгрузить чаты":
		if await is_superadmin_user(message.chat.id):
			await chats_download(message.chat.id)
		return

	if message.text == "Удалить бота из чата":
		groups = await db.get_groups()
		await bot.send_message(
			chat_id=message.chat.id,
			text="Выберите чат, из которого нужно удалить бота.",
			reply_markup=await build_group_markup(groups, page=0),
		)
		await admin_states.set(message.chat.id, "remove_group")
		return

	if message.text == "Уведомления о новых группах":
		updated = toggle_new_group_notifications(settings.runtime_settings_file)
		status = "включены" if updated.new_group_notifications_enabled else "выключены"
		await bot.send_message(
			chat_id=message.chat.id,
			text=f"Уведомления о новых группах {status}.",
		)
		return

	if state == "menu":
		await start(_, message)


@bot.on_message(filters.group & filters.text & filters.incoming)
async def group_messages_logs(_, message):
	await ensure_group_registered(message)
	member_title = await chat_member_title(message)
	await log_text_message(message, member_title)
	await handle_appeal(message, member_title)


@bot.on_message(filters.group & filters.document & filters.incoming)
async def group_documents_logs(_, message):
	await ensure_group_registered(message)
	member_title = await chat_member_title(message)
	await log_document_message(message, member_title)
	await handle_appeal(message, member_title)


@bot.on_message(filters.group & filters.photo & filters.incoming)
async def group_photo_logs(_, message):
	await ensure_group_registered(message)
	member_title = await chat_member_title(message)
	await log_photo_message(message, member_title)
	await handle_appeal(message, member_title)


@bot.on_callback_query()
async def query_handler(_, callback_query):
	state = await admin_states.get(callback_query.from_user.id)

	if callback_query.data == "rem":
		await callback_query.message.delete()
		return

	if callback_query.data.startswith("page_") and state == "remove_group":
		page = int(callback_query.data.split("_", 1)[1])
		groups = await db.get_groups()
		await callback_query.message.edit_reply_markup(await build_group_markup(groups, page))
		await callback_query.answer()
		return

	if state == "remove_group":
		try:
			group_id = int(callback_query.data)
			await db.remove_group(group_id)
			await callback_query.message.delete()
			await bot.leave_chat(group_id)
			await bot.send_message(
				chat_id=callback_query.from_user.id,
				text="Бот удален из выбранного чата.",
			)
			await admin_states.set(callback_query.from_user.id, "menu")
		except Exception as e:
			logger.error(f"Error removing group from callback {callback_query.data}: {e}")
			await bot.send_message(
				chat_id=callback_query.from_user.id,
				text="Не удалось удалить бота из чата. Попробуйте позже.",
			)


def run() -> None:
	if not settings.openai_api_key:
		logger.info("OPENAI_API_KEY is not configured; appeal classification, auto-replies and appeal reports are disabled")
	loop = asyncio.get_event_loop()
	loop.create_task(bootstrap_database_records())
	loop.create_task(run_daily_scheduler())

	logger.info("SherLegal group logger bot started")
	bot.run()
