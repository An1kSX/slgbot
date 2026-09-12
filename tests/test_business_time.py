from datetime import datetime, timezone

from slgbot.appeals import is_working_time
from slgbot.business_time import BUSINESS_TIMEZONE, tashkent_time
from slgbot.settings import Settings


def test_pyrogram_host_local_time_converts_to_tashkent():
    instant = datetime(2026, 5, 11, 19, 0, tzinfo=timezone.utc)
    pyrogram_date = datetime.fromtimestamp(instant.timestamp())
    assert tashkent_time(pyrogram_date) == datetime(2026, 5, 12, 0, 0, tzinfo=BUSINESS_TIMEZONE)


def test_working_hours_use_tashkent_even_for_utc_input():
    settings = Settings.from_env({"API_ID": "1", "API_HASH": "hash", "BOT_TOKEN": "123456789:test-secret"})
    assert is_working_time(datetime(2026, 5, 11, 4, 0, tzinfo=timezone.utc), settings)
    assert not is_working_time(datetime(2026, 5, 11, 13, 0, tzinfo=timezone.utc), settings)
