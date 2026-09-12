import asyncio
import importlib.util
import json
import zipfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from slgbot.business_time import BUSINESS_TIMEZONE
from slgbot.settings import Settings


@pytest.fixture
def logging_bot(tmp_path, monkeypatch):
    # Load the actual logging/export code without starting Telegram or MySQL.
    from slgbot import settings
    import sys

    config = Settings.from_env({
        "API_ID": "1", "API_HASH": "hash", "BOT_TOKEN": "123456789:test-secret",
        "GROUPS_DIR": str(tmp_path / "groups"),
        "LOG_ARCHIVE_DIR": str(tmp_path / "archive"),
        "HTML_TEMPLATE_DIR": str(Path("slgbot/templates").resolve()),
    })
    client = MagicMock()
    client.on_message.return_value = lambda handler: handler
    client.on_callback_query.return_value = lambda handler: handler
    client.send_document = AsyncMock()
    monkeypatch.setattr(settings, "get_settings", lambda: config)
    monkeypatch.setitem(sys.modules, "slgbot.bot_settings", SimpleNamespace(bot=client))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        spec = importlib.util.spec_from_file_location("logging_bot_under_test", "slgbot/bot.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        monkeypatch.chdir(tmp_path)
        yield module, client
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def message(chat_id, day, text):
    return SimpleNamespace(
        chat=SimpleNamespace(id=chat_id, title="Same title"),
        date=datetime(2026, 5, day, 12, tzinfo=BUSINESS_TIMEZONE),
        id=1, text=text, reply_to_message_id=None, from_user=None,
    )


def test_json_isolation_and_zip_contains_only_current_day(logging_bot, monkeypatch):
    module, client = logging_bot
    now = datetime(2026, 5, 12, 0, 1, tzinfo=BUSINESS_TIMEZONE)
    monkeypatch.setattr(module, "business_now", lambda: now)
    captured = {}

    async def capture_document(**kwargs):
        captured.update(kwargs)
        with zipfile.ZipFile(kwargs["document"]) as archive:
            captured["records"] = [
                json.loads(archive.read(name))
                for name in archive.namelist() if name.endswith("data.json")
            ]
            captured["names"] = archive.namelist()

    client.send_document.side_effect = capture_document

    async def scenario():
        await module.log_text_message(message(-1001, 11, "yesterday"))
        await module.log_text_message(message(-1001, 12, "first chat"))
        await module.log_text_message(message(-1002, 12, "second chat"))
        await module.chats_download(chat_id=123)

    asyncio.run(scenario())
    assert {record[0]["text"] for record in captured["records"]} == {"first chat", "second chat"}
    assert {record[0]["chat_id"] for record in captured["records"]} == {-1001, -1002}
    assert all(name.startswith("12.05.2026/") for name in captured["names"])
    assert "12.05.2026" in captured["caption"]
    assert "12.05.2026" in captured["document"]
    assert not Path(captured["document"]).exists()
