import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeSettings:
	new_group_notifications_enabled: bool = True


def load_runtime_settings(path: str | Path) -> RuntimeSettings:
	file_path = Path(path)
	if not file_path.exists():
		return RuntimeSettings()

	try:
		data = json.loads(file_path.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return RuntimeSettings()

	return RuntimeSettings(
		new_group_notifications_enabled=bool(
			data.get("new_group_notifications_enabled", True)
		)
	)


def save_runtime_settings(path: str | Path, settings: RuntimeSettings) -> None:
	file_path = Path(path)
	file_path.parent.mkdir(parents=True, exist_ok=True)
	file_path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")


def toggle_new_group_notifications(path: str | Path) -> RuntimeSettings:
	current = load_runtime_settings(path)
	updated = RuntimeSettings(
		new_group_notifications_enabled=not current.new_group_notifications_enabled
	)
	save_runtime_settings(path, updated)
	return updated
