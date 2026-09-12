from datetime import datetime, timezone

import pytest

from slgbot.business_time import BUSINESS_TIMEZONE
from slgbot.log_archiving import archive_group_logs, daily_logs_path, log_date_label


def test_manual_export_date_changes_at_tashkent_midnight():
    assert log_date_label(datetime(2026, 5, 11, 18, 59, tzinfo=timezone.utc)) == "11.05.2026"
    assert log_date_label(datetime(2026, 5, 11, 19, 0, tzinfo=timezone.utc)) == "12.05.2026"


@pytest.mark.parametrize("minute", [0, 30])
def test_archive_keeps_completed_day_label_and_leaves_today_untouched(tmp_path, minute):
    groups = tmp_path / "groups"
    archive = tmp_path / "archive"
    for day, text in [("11.05.2026", "yesterday"), ("12.05.2026", "today")]:
        folder = groups / day / "chat_-1001"
        folder.mkdir(parents=True)
        (folder / "data.json").write_text(text)
    now = datetime(2026, 5, 12, 0, minute, tzinfo=BUSINESS_TIMEZONE)

    assert archive_group_logs(groups, archive, now) == 1
    assert (archive / "11.05.2026/chat_-1001/data.json").read_text() == "yesterday"
    assert (daily_logs_path(groups, now) / "chat_-1001/data.json").read_text() == "today"
    assert not (groups / "11.05.2026").exists()
    assert archive_group_logs(groups, archive, now) == 0


def test_archiving_again_never_overwrites_existing_day(tmp_path):
    groups = tmp_path / "groups"
    archive = tmp_path / "archive"
    now = datetime(2026, 1, 1, tzinfo=BUSINESS_TIMEZONE)
    for text in ("first", "second", "third"):
        folder = groups / "31.12.2025" / "chat_-1001"
        folder.mkdir(parents=True)
        (folder / "data.json").write_text(text)
        assert archive_group_logs(groups, archive, now) == 1
    assert {path.read_text() for path in archive.rglob("data.json")} == {"first", "second", "third"}
