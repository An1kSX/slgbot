from datetime import datetime, timedelta, time
from types import SimpleNamespace

from appeals import (
    is_client_user,
    is_working_time,
    message_text,
    should_handle_appeal,
)
from settings import Settings


def make_settings(**overrides):
    values = {
        "api_id": 1,
        "api_hash": "hash",
        "bot_token": "token",
        "session_name": "testbot",
        "bot_user_id": 999,
        "bot_username": "slgbot",
        "staff_marker": "SLG",
        "staff_usernames": set(),
        "staff_user_ids": set(),
        "working_days": {0, 1, 2, 3, 4, 5},
        "work_start": time(9, 0),
        "work_end": time(18, 0),
        "appeal_auto_reply": "We will answer during business hours.",
        "appeal_cooldown_seconds": 15 * 60 * 60,
        "appeal_report_time": "09:00",
        "groups_dir": "groups",
        "log_archive_dir": "archive",
        "html_template_dir": "src",
        "max_document_mb": 50,
        "log_zip_prefix": "slg_chats",
        "superadmin_ids": {1},
        "admin_ids": set(),
        "openai_api_key": None,
        "openai_model": "gpt-4o-mini",
        "mysql_host": None,
        "mysql_port": 3306,
        "mysql_user": None,
        "mysql_password": None,
        "mysql_database": None,
        "mysql_queue_size": 10,
        "log_file": "logs.log",
        "runtime_settings_file": "runtime_settings.json",
        "log_archive_time": "00:00",
        "log_date_offset_minutes": 25,
    }
    values.update(overrides)
    return Settings(**values)


def user(**kwargs):
    values = {
        "id": 10,
        "first_name": "Client",
        "last_name": "",
        "username": "client",
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def message(**kwargs):
    values = {
        "text": "Need legal advice",
        "caption": None,
        "from_user": user(),
        "date": datetime(2026, 5, 11, 20, 0),
        "outgoing": False,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_is_client_user_detects_slg_in_name_username_title_and_ids():
    settings = make_settings(staff_usernames={"legal"}, staff_user_ids={42})

    assert not is_client_user(user(first_name="SLG Anna"), None, settings)
    assert not is_client_user(user(username="legal"), None, settings)
    assert not is_client_user(user(id=42), None, settings)
    assert not is_client_user(user(), "Senior SLG lawyer", settings)
    assert is_client_user(user(first_name="Client"), None, settings)


def test_is_working_time_uses_monday_to_saturday_schedule():
    settings = make_settings()

    assert is_working_time(datetime(2026, 5, 11, 9, 0), settings)
    assert is_working_time(datetime(2026, 5, 16, 17, 59), settings)
    assert not is_working_time(datetime(2026, 5, 16, 18, 0), settings)
    assert not is_working_time(datetime(2026, 5, 17, 12, 0), settings)


def test_message_text_prefers_text_then_caption():
    assert message_text(message(text="hello", caption="caption")) == "hello"
    assert message_text(message(text=None, caption="caption")) == "caption"
    assert message_text(message(text=None, caption=None)) == ""


def test_should_handle_appeal_requires_after_hours_client_business_message():
    settings = make_settings()
    msg = message()

    assert should_handle_appeal(
        msg,
        chat_member_title=None,
        settings=settings,
        is_business_message=True,
        has_active_cooldown=False,
    )
    assert not should_handle_appeal(
        message(date=datetime(2026, 5, 11, 10, 0)),
        chat_member_title=None,
        settings=settings,
        is_business_message=True,
        has_active_cooldown=False,
    )
    assert not should_handle_appeal(
        message(from_user=user(first_name="SLG Anna")),
        chat_member_title=None,
        settings=settings,
        is_business_message=True,
        has_active_cooldown=False,
    )
    assert not should_handle_appeal(
        msg,
        chat_member_title=None,
        settings=settings,
        is_business_message=False,
        has_active_cooldown=False,
    )
    assert not should_handle_appeal(
        msg,
        chat_member_title=None,
        settings=settings,
        is_business_message=True,
        has_active_cooldown=True,
    )
