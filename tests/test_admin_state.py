import asyncio

from slgbot.admin_state import AdminStateStore


def test_env_admin_state_is_kept_even_without_database_row():
    saved_states = []

    async def get_state(admin_id):
        return "menu"

    async def set_state(admin_id, state):
        saved_states.append((admin_id, state))
        return False

    store = AdminStateStore({10}, get_state, set_state)

    asyncio.run(store.set(10, "remove_group"))

    assert asyncio.run(store.get(10)) == "remove_group"
    assert saved_states == [(10, "remove_group")]


def test_database_admin_state_uses_database_when_not_env_admin():
    state = "menu"

    async def get_state(admin_id):
        return state

    async def set_state(admin_id, new_state):
        nonlocal state
        state = new_state
        return True

    store = AdminStateStore(set(), get_state, set_state)

    asyncio.run(store.set(20, "remove_group"))

    assert asyncio.run(store.get(20)) == "remove_group"
