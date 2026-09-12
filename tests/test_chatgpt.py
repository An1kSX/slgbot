import asyncio
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from slgbot import chatgpt
from slgbot.settings import Settings


@pytest.mark.parametrize("key", [None, "", "   "])
def test_no_api_key_never_creates_llm_client_or_accepts_message(monkeypatch, key):
    settings = Settings.from_env({"API_ID": "1", "API_HASH": "hash", "BOT_TOKEN": "123:test-secret"})
    settings = replace(settings, openai_api_key=key)
    client = MagicMock()
    monkeypatch.setattr(chatgpt, "AsyncOpenAI", client)
    assert asyncio.run(chatgpt.is_business_message("Need legal advice", settings)) is False
    client.assert_not_called()
