from datetime import datetime, time, timezone
from types import SimpleNamespace
from pathlib import Path

from slgbot.chat_to_html import add_html_record, create_html_file, html_path_builder, safe_chat_dir_name
from slgbot.business_time import BUSINESS_TIMEZONE
from slgbot.settings import Settings


def make_settings(tmp_path):
    return Settings(
        api_id=1,
        api_hash="hash",
        bot_token="token",
        session_name="testbot",
        bot_user_id=999,
        bot_username="slgbot",
        staff_marker="SLG",
        staff_usernames=set(),
        staff_user_ids=set(),
        working_days={0, 1, 2, 3, 4, 5},
        work_start=time(9, 0),
        work_end=time(18, 0),
        appeal_auto_reply="reply",
        appeal_cooldown_seconds=1,
        appeal_report_time="09:00",
        groups_dir=str(tmp_path / "groups"),
        log_archive_dir=str(tmp_path / "archive"),
        html_template_dir=str(tmp_path / "src"),
        max_document_mb=50,
        log_zip_prefix="slg",
        superadmin_ids={1},
        admin_ids=set(),
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        mysql_host=None,
        mysql_port=3306,
        mysql_user=None,
        mysql_password=None,
        mysql_database=None,
        mysql_queue_size=10,
        log_file="logs.log",
        runtime_settings_file="runtime_settings.json",
        log_archive_time="00:00",
    )


def create_assets(template_dir):
    template_dir.mkdir(parents=True)
    (template_dir / "chat_export.html").write_text("<title>ChatNaMe</title>", encoding="utf-8")
    (template_dir / "styles.css").write_text("body{}", encoding="utf-8")
    (template_dir / "scripts.js").write_text("", encoding="utf-8")
    (template_dir / "avatar.png").write_bytes(b"avatar")
    (template_dir / "file.png").write_bytes(b"file")


def test_safe_chat_dir_name_removes_path_separators():
    assert safe_chat_dir_name('SLG/Client: "A"') == "SLG_Client_A"


def test_html_path_builder_uses_configured_groups_dir(tmp_path):
    settings = make_settings(tmp_path)

    result = html_path_builder(-100123, datetime(2026, 5, 11, 12, tzinfo=BUSINESS_TIMEZONE), settings)

    assert result == tmp_path / "groups" / "11.05.2026" / "chat_-100123" / "chat_export"


def test_create_html_file_copies_configured_assets(tmp_path):
    settings = make_settings(tmp_path)
    create_assets(tmp_path / "src")
    file_path = html_path_builder(123, datetime(2026, 5, 11, 12, tzinfo=BUSINESS_TIMEZONE), settings)

    create_html_file(123, "SherLegal", file_path, settings)

    assert (file_path / "chat_export.html").read_text(encoding="utf-8") == "<title>SherLegal</title>"
    assert (file_path / "css" / "styles.css").read_text(encoding="utf-8") == "body{}"
    assert (file_path / "js" / "scripts.js").read_text(encoding="utf-8") == ""
    assert (file_path / "img" / "avatar.png").read_bytes() == b"avatar"
    assert (file_path / "img" / "file.png").read_bytes() == b"file"


def test_same_title_chats_stay_separate_and_rename_keeps_history(tmp_path):
    settings = make_settings(tmp_path)
    create_assets(tmp_path / "src")
    moment = datetime(2026, 5, 11, 12, tzinfo=BUSINESS_TIMEZONE)

    def write(chat_id, title, text, message_id):
        add_html_record(SimpleNamespace(
            chat=SimpleNamespace(id=chat_id, title=title), date=moment,
            id=message_id, text=text, from_user=None,
        ), settings=settings)

    write(-1001, "Same title", "first chat", 1)
    write(-1002, "Same title", "second chat", 1)
    write(-1001, "Renamed chat", "after rename", 2)
    first = html_path_builder(-1001, moment, settings)
    second = html_path_builder(-1002, moment, settings)
    first_js = (first / "js/scripts.js").read_text(encoding="utf-8")
    second_js = (second / "js/scripts.js").read_text(encoding="utf-8")
    assert "first chat" in first_js and "after rename" in first_js
    assert "second chat" not in first_js
    assert "second chat" in second_js and "first chat" not in second_js


def test_messages_crossing_tashkent_midnight_use_separate_days(tmp_path):
    settings = make_settings(tmp_path)
    before = html_path_builder(-1001, datetime(2026, 5, 11, 18, 59, tzinfo=timezone.utc), settings)
    after = html_path_builder(-1001, datetime(2026, 5, 11, 19, 0, tzinfo=timezone.utc), settings)
    assert before.parent.parent.name == "11.05.2026"
    assert after.parent.parent.name == "12.05.2026"


def test_packaged_templates_work_outside_project_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings.from_env({"API_ID": "1", "API_HASH": "hash", "BOT_TOKEN": "123456789:test-secret"})
    export = tmp_path / "export"
    create_html_file(-1001, "Customer chat", export, settings)
    assert "Customer chat" in (export / "chat_export.html").read_text(encoding="utf-8")
    for asset in ("css/styles.css", "js/scripts.js", "img/avatar.png", "img/file.png"):
        assert (export / asset).is_file()
