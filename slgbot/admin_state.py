from collections.abc import Awaitable, Callable


class AdminStateStore:
	def __init__(
		self,
		env_admin_ids: set[int],
		get_state: Callable[[int], Awaitable[str]],
		set_state: Callable[[int, str], Awaitable[bool]],
	):
		self._env_admin_ids = env_admin_ids
		self._get_state = get_state
		self._set_state = set_state
		self._memory_states: dict[int, str] = {}

	async def get(self, admin_id: int) -> str:
		if admin_id in self._memory_states:
			return self._memory_states[admin_id]
		return await self._get_state(admin_id)

	async def set(self, admin_id: int, state: str) -> bool:
		if admin_id in self._env_admin_ids:
			self._memory_states[admin_id] = state
		return await self._set_state(admin_id, state)
