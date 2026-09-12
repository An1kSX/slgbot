from pathlib import Path


def test_bot_has_no_removed_business_features():
    source = Path("slgbot/bot.py").read_text(encoding="utf-8")

    forbidden = [
        "bitrix_module",
        "html_report_parser",
        "pandas",
        "requests",
        "InputMedia",
        "increase_score",
        "decrease_score",
        "bx24.create_task",
        "mass_forward",
        "quick_questions",
        "ATB",
        "atbconsultbot",
    ]

    for token in forbidden:
        assert token not in source


def test_chatgpt_only_exposes_business_classifier():
    source = Path("slgbot/chatgpt.py").read_text(encoding="utf-8")

    forbidden = [
        "sk-",
        "translate",
        "user_qw",
        "analize_accountants",
        "generate_anniversary",
        "EmployeesReport",
    ]

    for token in forbidden:
        assert token not in source

    assert "is_business_message" in source


def test_removed_integration_modules_are_absent():
    removed_files = [
        "api_client.py",
        "bitrix_module.py",
        "database_old.py",
        "html_report_parser.py",
    ]

    for file_name in removed_files:
        assert not Path(file_name).exists()


def test_bot_uses_safe_appeal_clear_and_runtime_group_notifications():
    source = Path("slgbot/bot.py").read_text(encoding="utf-8")

    assert "groups_clear_appeal_by_ids" in source
    assert "await db.groups_clear_appeal()" not in source
    assert "toggle_new_group_notifications" in source
    assert "notify_new_group" in source
    assert "await message.chat.leave()" not in source
