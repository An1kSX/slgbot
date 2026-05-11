from datetime import datetime

from log_archiving import log_date_label


def test_log_date_label_uses_previous_day_at_midnight_with_offset():
    assert log_date_label(datetime(2026, 5, 12, 0, 0), 25) == "11.05.2026"


def test_log_date_label_uses_same_day_after_offset_window():
    assert log_date_label(datetime(2026, 5, 12, 0, 30), 25) == "12.05.2026"
