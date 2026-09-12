from datetime import datetime
from pathlib import Path
from shutil import move
from uuid import uuid4

from slgbot.business_time import tashkent_time


def log_date_label(moment: datetime) -> str:
	return tashkent_time(moment).strftime("%d.%m.%Y")


def daily_logs_path(groups_dir: str | Path, moment: datetime) -> Path:
	return Path(groups_dir) / log_date_label(moment)


def archive_group_logs(
	groups_dir: str | Path,
	archive_dir: str | Path,
	moment: datetime,
) -> int:
	source_path = Path(groups_dir)
	if not source_path.exists():
		return 0

	today = tashkent_time(moment).date()
	destination_root = Path(archive_dir)

	moved = 0
	for item in source_path.iterdir():
		if not item.is_dir():
			continue
		try:
			log_day = datetime.strptime(item.name, "%d.%m.%Y").date()
		except ValueError:
			continue
		if log_day >= today:
			continue

		destination_root.mkdir(parents=True, exist_ok=True)
		target = destination_root / item.name
		if target.exists():
			target = destination_root / f"{item.name}_{uuid4().hex}"

		chat_count = sum(child.is_dir() for child in item.iterdir())
		move(str(item), str(target))
		moved += chat_count

	return moved
