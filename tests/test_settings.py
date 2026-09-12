from datetime import time

import pytest

from slgbot.settings import Settings, parse_csv_ints, parse_csv_strings, parse_time


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
            "BOT_TOKEN": "123456789:test-secret",
            "SUPERADMIN_IDS": "10,20",
        }
    )

    assert settings.api_id == 123
    assert settings.api_hash == "hash"
    assert settings.bot_token == "123456789:test-secret"
    assert settings.bot_user_id == 123456789
    assert settings.staff_marker == "SLG"
    assert settings.working_days == {0, 1, 2, 3, 4, 5}
    assert settings.work_start == time(9, 0)
    assert settings.work_end == time(18, 0)
    assert settings.superadmin_ids == {10, 20}
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.runtime_settings_file == "data/runtime/runtime_settings.json"
    assert settings.log_archive_time == "00:00"


def test_bot_id_comes_from_token_even_with_stale_env_id():
    settings = Settings.from_env({
        "API_ID": "123", "API_HASH": "hash", "BOT_TOKEN": "987654321:test-secret",
        "BOT_USER_ID": "111111111",
    })
    assert settings.bot_user_id == 987654321


@pytest.mark.parametrize("key", ["", "   "])
def test_empty_openai_key_is_disabled(key):
    settings = Settings.from_env({
        "API_ID": "123", "API_HASH": "hash", "BOT_TOKEN": "123:test-secret",
        "OPENAI_API_KEY": key,
    })
    assert settings.openai_api_key is None


@pytest.mark.parametrize("token", ["secret-without-id", "abc:private-secret", "123:", "0:private-secret"])
def test_invalid_token_reports_format_error_without_leaking_token(token):
    with pytest.raises(ValueError, match="BOT_TOKEN") as error:
        Settings.from_env({"API_ID": "123", "API_HASH": "hash", "BOT_TOKEN": token})
    assert token not in str(error.value)
