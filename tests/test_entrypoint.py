import asyncio
import runpy
import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace


def test_module_entrypoint_runs_bot_with_an_event_loop(monkeypatch):
    calls = []

    def fake_run():
        calls.append(asyncio.get_event_loop())

    monkeypatch.setitem(sys.modules, "slgbot.bot", SimpleNamespace(run=fake_run))
    try:
        runpy.run_module("slgbot", run_name="__main__")
        assert len(calls) == 1
        assert not calls[0].is_closed()
    finally:
        for loop in calls:
            loop.close()
        asyncio.set_event_loop(None)


def test_real_pyrogram_lifecycle_uses_one_main_thread_loop(tmp_path):
    probe = Path(__file__).parent / "probes" / "pyrogram_startup.py"
    result = subprocess.run(
        [sys.executable, "-c", probe.read_text(encoding="utf-8"), str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "main thread event loop: OK" in result.stdout
