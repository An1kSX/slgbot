from pathlib import Path


def test_db_functions_has_no_external_business_integrations():
    source = Path("slgbot/db_functions.py").read_text(encoding="utf-8")

    forbidden = [
        "APIClient",
        "BITRIX",
        "bitrix",
        "aiohttp",
        "increase_score",
        "decrease_score",
        "reset_score",
        "send_report",
        "get_anniversaries",
        "get_monthly_reports",
    ]

    for token in forbidden:
        assert token not in source


def test_db_functions_can_clear_specific_appeal_groups():
    source = Path("slgbot/db_functions.py").read_text(encoding="utf-8")

    assert "groups_clear_appeal_by_ids" in source
    assert "WHERE id IN" in source


def test_db_functions_bootstraps_env_admins():
    source = Path("slgbot/db_functions.py").read_text(encoding="utf-8")

    assert "bootstrap_admins" in source
    assert "ON DUPLICATE KEY UPDATE" in source
