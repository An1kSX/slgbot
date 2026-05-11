from datetime import datetime, timedelta
from pathlib import Path
from shutil import move


def log_date_label(moment: datetime, offset_minutes: int) -> str:
	log_date = moment - timedelta(minutes=offset_minutes)
	return log_date.strftime("%d.%m.%Y")


def archive_group_logs(
	groups_dir: str | Path,
	archive_dir: str | Path,
	moment: datetime,
	offset_minutes: int,
) -> int:
	source_path = Path(groups_dir)
	if not source_path.exists():
		return 0

	destination_root = Path(archive_dir) / log_date_label(moment, offset_minutes)
	destination_root.mkdir(parents=True, exist_ok=True)

	moved = 0
	for item in source_path.iterdir():
		if not item.is_dir():
			continue

		target = destination_root / item.name
		if target.exists():
			target = destination_root / f"{item.name}_{moment.strftime('%H%M%S')}"

		move(str(item), str(target))
		moved += 1

	return moved
