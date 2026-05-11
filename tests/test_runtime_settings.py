from runtime_settings import (
    RuntimeSettings,
    load_runtime_settings,
    toggle_new_group_notifications,
)


def test_runtime_settings_default_enables_new_group_notifications(tmp_path):
    settings = load_runtime_settings(tmp_path / "runtime.json")

    assert settings.new_group_notifications_enabled is True


def test_toggle_new_group_notifications_persists_value(tmp_path):
    path = tmp_path / "runtime.json"

    updated = toggle_new_group_notifications(path)

    assert updated.new_group_notifications_enabled is False
    assert load_runtime_settings(path).new_group_notifications_enabled is False
