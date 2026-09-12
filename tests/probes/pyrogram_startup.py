"""Offline probe of the real Pyrogram lifecycle in a fresh Python process."""

import asyncio
import importlib
import inspect
import os
from pathlib import Path
import socket
import sys
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import dotenv


# Never read deployment credentials or open a real Telegram session in this probe.
dotenv.load_dotenv = lambda *args, **kwargs: False
os.environ.update({
    "API_ID": "123",
    "API_HASH": "test-hash",
    "BOT_TOKEN": "123456789:test-secret",
    "OPENAI_API_KEY": "",
    "SUPERADMIN_IDS": "",
    "ADMIN_IDS": "",
    "LOG_FILE": str(Path(sys.argv[1]) / "startup.log"),
})

from slgbot.__main__ import main


events = []
state = {}
original_set_loop = asyncio.set_event_loop


def prepare_probe(loop):
    original_set_loop(loop)
    asyncio.set_event_loop = original_set_loop
    assert threading.current_thread() is threading.main_thread()

    # Import the real app only after its entrypoint installs the loop.
    from slgbot import bot as app
    from pyrogram import Client
    from pyrogram.sync import async_to_sync

    client = app.bot
    state.update(loop=loop, client=client)
    assert client.loop is loop
    assert client.dispatcher.loop is loop
    for method in (Client.start, Client.stop, Client.get_me):
        assert inspect.getclosurevars(method).nonlocals["main_loop"] is loop

    def record(name):
        assert threading.current_thread() is threading.main_thread(), name
        assert asyncio.get_running_loop() is loop, name
        events.append(name)

    def only_loopback(original):
        def connect_socket(sock, address):
            # Windows asyncio uses a loopback socket pair for its internal wakeup pipe.
            if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
                raise AssertionError("The startup probe must not access external services")
            return original(sock, address)
        return connect_socket

    socket.socket.connect = only_loopback(socket.socket.connect)
    socket.socket.connect_ex = only_loopback(socket.socket.connect_ex)

    async def connect():
        record("connect")
        client.is_connected = True
        return True

    async def disconnect():
        record("disconnect")
        client.is_connected = False

    async def invoke(self, query, *args, **kwargs):
        record("thread-call" if isinstance(query, str) and query == "thread-probe" else "invoke")

    async def bootstrap():
        record("bootstrap")

    async def scheduler():
        record("scheduler")

    async def idle():
        record("idle")
        assert client.is_initialized
        assert len(client.dispatcher.handler_worker_tasks) == 2
        assert all(task.get_loop() is loop for task in client.dispatcher.handler_worker_tasks)

        def from_worker():
            assert threading.current_thread() is not threading.main_thread()
            # Exercise Pyrogram's actual thread-to-main-loop sync wrapper.
            try:
                return client.invoke("thread-probe")
            finally:
                worker_loop = asyncio.get_event_loop()
                assert worker_loop is not loop
                worker_loop.close()
                asyncio.set_event_loop(None)

        await asyncio.wait_for(loop.run_in_executor(client.executor, from_worker), timeout=5)

    # Keep Client.run/start/initialize/stop/terminate and Dispatcher unchanged.
    # Replace only external IO, business tasks, and indefinite idle waiting.
    client.connect = connect
    client.disconnect = disconnect
    client.get_me = AsyncMock(return_value=SimpleNamespace(id=123456789, is_bot=True))
    client.storage = SimpleNamespace(is_bot=AsyncMock(return_value=True), save=AsyncMock())
    client.workers = 2
    Client.invoke = invoke
    async_to_sync(Client, "invoke")
    app.bootstrap_database_records = bootstrap
    app.run_daily_scheduler = scheduler
    importlib.import_module("pyrogram.methods.utilities.run").idle = idle


asyncio.set_event_loop = prepare_probe
try:
    main()
    assert {"connect", "invoke", "bootstrap", "scheduler", "idle", "thread-call", "disconnect"} <= set(events), events
    assert not state["client"].is_initialized
    assert not state["client"].is_connected
    assert not asyncio.all_tasks(state["loop"])
    print("Pyrogram lifecycle and worker call used the main thread event loop: OK")
finally:
    asyncio.set_event_loop = original_set_loop
    if "client" in state:
        state["client"].executor.shutdown(wait=True)
    if "loop" in state:
        loop = state["loop"]
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
    original_set_loop(None)
