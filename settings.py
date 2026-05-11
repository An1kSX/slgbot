import os
from dataclasses import dataclass
from datetime import time
from functools import lru_cache
from typing import Mapping


def parse_csv_ints(value: str | None) -> set[int]:
	if not value:
		return set()
	return {int(item.strip()) for item in value.split(",") if item.strip()}


def parse_csv_strings(value: str | None) -> set[str]:
	if not value:
		return set()
	return {item.strip().lower() for item in value.split(",") if item.strip()}


def parse_time(value: str) -> time:
	hour, minute = value.split(":", 1)
	return time(int(hour), int(minute))


def env_int(env: Mapping[str, str], key: str, default: int | None = None) -> int:
	value = env.get(key)
	if value is None or value == "":
		if default is None:
			raise ValueError(f"Missing required environment variable: {key}")
		return default
	return int(value)


def env_str(env: Mapping[str, str], key: str, default: str | None = None) -> str:
	value = env.get(key)
	if value is None or value == "":
		if default is None:
			raise ValueError(f"Missing required environment variable: {key}")
		return default
	return value


@dataclass(frozen=True)
class Settings:
	api_id: int
	api_hash: str
	bot_token: str
	session_name: str
	bot_user_id: int | None
	bot_username: str
	staff_marker: str
	staff_usernames: set[str]
	staff_user_ids: set[int]
	working_days: set[int]
	work_start: time
	work_end: time
	appeal_auto_reply: str
	appeal_cooldown_seconds: int
	appeal_report_time: str
	groups_dir: str
	log_archive_dir: str
	html_template_dir: str
	max_document_mb: int
	log_zip_prefix: str
	superadmin_ids: set[int]
	admin_ids: set[int]
	openai_api_key: str | None
	openai_model: str
	mysql_host: str | None
	mysql_port: int
	mysql_user: str | None
	mysql_password: str | None
	mysql_database: str | None
	mysql_queue_size: int
	log_file: str
	runtime_settings_file: str
	log_archive_time: str
	log_date_offset_minutes: int

	@classmethod
	def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
		env = env or os.environ
		return cls(
			api_id=env_int(env, "API_ID"),
			api_hash=env_str(env, "API_HASH"),
			bot_token=env_str(env, "BOT_TOKEN"),
			session_name=env.get("SESSION_NAME", "slgbot"),
			bot_user_id=int(env["BOT_USER_ID"]) if env.get("BOT_USER_ID") else None,
			bot_username=env.get("BOT_USERNAME", ""),
			staff_marker=env.get("STAFF_MARKER", "SLG"),
			staff_usernames=parse_csv_strings(env.get("STAFF_USERNAMES")),
			staff_user_ids=parse_csv_ints(env.get("STAFF_USER_IDS")),
			working_days=parse_csv_ints(env.get("WORKING_DAYS", "0,1,2,3,4,5")),
			work_start=parse_time(env.get("WORK_START", "09:00")),
			work_end=parse_time(env.get("WORK_END", "18:00")),
			appeal_auto_reply=env.get(
				"APPEAL_AUTO_REPLY",
				"Thank you for your message. We will respond during SherLegal business hours.",
			),
			appeal_cooldown_seconds=env_int(env, "APPEAL_COOLDOWN_SECONDS", 15 * 60 * 60),
			appeal_report_time=env.get("APPEAL_REPORT_TIME", "09:00"),
			groups_dir=env.get("GROUPS_DIR", "groups"),
			log_archive_dir=env.get("LOG_ARCHIVE_DIR", "archive"),
			html_template_dir=env.get("HTML_TEMPLATE_DIR", "src"),
			max_document_mb=env_int(env, "MAX_DOCUMENT_MB", 50),
			log_zip_prefix=env.get("LOG_ZIP_PREFIX", "slg_chats"),
			superadmin_ids=parse_csv_ints(env.get("SUPERADMIN_IDS")),
			admin_ids=parse_csv_ints(env.get("ADMIN_IDS")),
			openai_api_key=env.get("OPENAI_API_KEY"),
			openai_model=env.get("OPENAI_MODEL", "gpt-4o-mini"),
			mysql_host=env.get("MYSQL_HOST"),
			mysql_port=env_int(env, "MYSQL_PORT", 3306),
			mysql_user=env.get("MYSQL_USER"),
			mysql_password=env.get("MYSQL_PASSWORD"),
			mysql_database=env.get("MYSQL_DATABASE"),
			mysql_queue_size=env_int(env, "MYSQL_QUEUE_SIZE", 10),
			log_file=env.get("LOG_FILE", "logs.log"),
			runtime_settings_file=env.get("RUNTIME_SETTINGS_FILE", "runtime_settings.json"),
			log_archive_time=env.get("LOG_ARCHIVE_TIME", "00:00"),
			log_date_offset_minutes=env_int(env, "LOG_DATE_OFFSET_MINUTES", 25),
		)

	def is_admin_id(self, user_id: int) -> bool:
		return user_id in self.admin_ids or user_id in self.superadmin_ids

	def is_superadmin_id(self, user_id: int) -> bool:
		return user_id in self.superadmin_ids


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings.from_env()
