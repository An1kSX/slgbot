import asyncio
import runpy
import sys
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
