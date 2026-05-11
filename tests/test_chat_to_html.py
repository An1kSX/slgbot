from datetime import datetime, time
from types import SimpleNamespace

from chat_to_html import create_html_file, html_path_builder, safe_chat_dir_name
from settings import Settings


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
        log_date_offset_minutes=25,
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

    result = html_path_builder("SLG/Client", settings)

    assert result == tmp_path / "groups" / "SLG_Client" / "chat_export"


def test_create_html_file_copies_configured_assets(tmp_path):
    settings = make_settings(tmp_path)
    create_assets(tmp_path / "src")
    file_path = html_path_builder("SherLegal", settings)

    create_html_file(123, "SherLegal", file_path, settings)

    assert (file_path / "chat_export.html").read_text(encoding="utf-8") == "<title>SherLegal</title>"
    assert (file_path / "css" / "styles.css").read_text(encoding="utf-8") == "body{}"
    assert (file_path / "js" / "scripts.js").read_text(encoding="utf-8") == ""
    assert (file_path / "img" / "avatar.png").read_bytes() == b"avatar"
    assert (file_path / "img" / "file.png").read_bytes() == b"file"
