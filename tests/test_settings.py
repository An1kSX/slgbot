from datetime import time

from settings import Settings, parse_csv_ints, parse_csv_strings, parse_time


def test_parse_csv_ints_ignores_empty_values():
    assert parse_csv_ints("1, 2,,3") == {1, 2, 3}


def test_parse_csv_strings_normalizes_case():
    assert parse_csv_strings("SLGUser,  Legal_Team ") == {"slguser", "legal_team"}


def test_parse_time_accepts_hour_minute():
    assert parse_time("09:30") == time(9, 30)


def test_settings_from_env_uses_slg_defaults():
    settings = Settings.from_env(
        {
            "API_ID": "123",
            "API_HASH": "hash",
            "BOT_TOKEN": "token",
            "SUPERADMIN_IDS": "10,20",
        }
    )

    assert settings.api_id == 123
    assert settings.api_hash == "hash"
    assert settings.bot_token == "token"
    assert settings.staff_marker == "SLG"
    assert settings.working_days == {0, 1, 2, 3, 4, 5}
    assert settings.work_start == time(9, 0)
    assert settings.work_end == time(18, 0)
    assert settings.superadmin_ids == {10, 20}
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.runtime_settings_file == "runtime_settings.json"
    assert settings.log_archive_time == "00:00"
    assert settings.log_date_offset_minutes == 25
