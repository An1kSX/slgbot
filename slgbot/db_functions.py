import time

from slgbot.database import database as db
from slgbot.logger import logger


async def get_group_title(group_id: int) -> str:
	try:
		res = await db.execute_query("SELECT name FROM groups WHERE id = %s", (group_id,))
		return res[0][0] if res else str(group_id)
	except Exception as e:
		logger.error(f"Error getting group title for {group_id}: {e}")
		return str(group_id)


async def get_groups() -> list:
	return await db.execute_query("SELECT name, id FROM groups ORDER BY name")


async def get_admins() -> list:
	return await db.execute_query("SELECT name, id FROM admins")


async def get_super_admins() -> list:
	return await db.execute_query("SELECT name, id FROM admins WHERE superadmin = TRUE")


async def bootstrap_admins(admin_ids: set[int], superadmin_ids: set[int]) -> None:
	all_admin_ids = set(admin_ids) | set(superadmin_ids)
	for admin_id in all_admin_ids:
		is_superadmin_value = admin_id in superadmin_ids
		await db.execute_query(
			"""
			INSERT INTO admins (id, superadmin, name, state, dialog)
			VALUES (%s, %s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE
				superadmin = IF(VALUES(superadmin), TRUE, superadmin),
				name = IF(name = '', VALUES(name), name),
				state = IF(state = '', VALUES(state), state),
				dialog = IF(dialog IS NULL, VALUES(dialog), dialog)
			""",
			(
				admin_id,
				is_superadmin_value,
				f"Admin {admin_id}",
				"menu",
				"",
			),
		)


async def is_superadmin(admin_id: int) -> bool:
	res = await db.execute_query(
		"SELECT id FROM admins WHERE id = %s AND superadmin = TRUE",
		(admin_id,),
	)
	return bool(res)


async def is_admin(admin_id: int) -> bool:
	res = await db.execute_query("SELECT id FROM admins WHERE id = %s", (admin_id,))
	return bool(res)


async def add_group(group_id: int, group_name: str) -> bool:
	try:
		await db.execute_query(
			"""
			INSERT INTO groups (id, name, timestp, has_appeal)
			VALUES (%s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE name = VALUES(name)
			""",
			(group_id, group_name, 0, False),
		)
		return True
	except Exception as e:
		logger.error(f"Error adding group {group_name} ({group_id}): {e}")
		return False


async def remove_group(group_id: int) -> bool:
	try:
		await db.execute_query("DELETE FROM groups WHERE id = %s", (group_id,))
		return True
	except Exception as e:
		logger.error(f"Error removing group {group_id}: {e}")
		return False


async def change_group(group_name: str, group_id: int) -> bool:
	try:
		await db.execute_query("UPDATE groups SET id = %s WHERE name = %s", (group_id, group_name))
		return True
	except Exception as e:
		logger.error(f"Error changing group id for {group_name}: {e}")
		return False


async def update_group_title(group_id: int, title: str) -> bool:
	try:
		await db.execute_query("UPDATE groups SET name = %s WHERE id = %s", (title, group_id))
		return True
	except Exception as e:
		logger.error(f"Error updating group title for {group_id}: {e}")
		return False


async def groups_with_appeal() -> list:
	return await db.execute_query("SELECT name, id FROM groups WHERE has_appeal = %s ORDER BY name", (1,))


async def groups_clear_appeal() -> None:
	await db.execute_query("UPDATE groups SET has_appeal = %s", (0,))


async def groups_clear_appeal_by_ids(group_ids: list[int]) -> None:
	if not group_ids:
		return

	placeholders = ", ".join(["%s"] * len(group_ids))
	await db.execute_query(
		f"UPDATE groups SET has_appeal = %s WHERE id IN ({placeholders})",
		(0, *group_ids),
	)


async def group_change_appeal(group_id: int, has_appeal: bool) -> None:
	await db.execute_query(
		"UPDATE groups SET has_appeal = %s WHERE id = %s",
		(has_appeal, group_id),
	)


async def group_has_appeal(group_id: int) -> bool:
	res = await db.execute_query(
		"SELECT id FROM groups WHERE has_appeal = %s AND id = %s",
		(1, group_id),
	)
	return bool(res)


async def group_has_apeal(group_id: int) -> bool:
	return await group_has_appeal(group_id)


async def set_group_cooldown(group_id: int, ttl_seconds: int) -> None:
	expires_at = str(time.time() + ttl_seconds)
	await db.execute_query("UPDATE groups SET timestp = %s WHERE id = %s", (expires_at, group_id))


async def group_has_active_cooldown(group_id: int) -> bool:
	res = await db.execute_query("SELECT timestp FROM groups WHERE id = %s", (group_id,))
	if not res:
		return False
	try:
		return float(res[0][0]) > time.time()
	except (TypeError, ValueError):
		return False


async def set_timestp(group_id: int, ttl_seconds: int = 15 * 60 * 60) -> None:
	await set_group_cooldown(group_id, ttl_seconds)


async def get_timestp(group_id: int) -> bool:
	return not await group_has_active_cooldown(group_id)


async def set_admin_id(admin_id: int) -> bool:
	try:
		await db.execute_query(
			"INSERT INTO admins (id, superadmin, name, state, dialog) VALUES (%s, %s, %s, %s, %s)",
			(admin_id, False, "New admin", "menu", ""),
		)
		return True
	except Exception as e:
		logger.error(f"Error adding admin {admin_id}: {e}")
		return False


async def set_admin_name(admin_name: str) -> bool:
	try:
		await db.execute_query(
			"UPDATE admins SET name = %s WHERE name = %s",
			(admin_name, "New admin"),
		)
		return True
	except Exception as e:
		logger.error(f"Error setting admin name {admin_name}: {e}")
		return False


async def remove_admin(admin_id: int) -> bool:
	if await is_superadmin(admin_id):
		return False
	try:
		await db.execute_query("DELETE FROM admins WHERE id = %s", (admin_id,))
		return True
	except Exception as e:
		logger.error(f"Error removing admin {admin_id}: {e}")
		return False


async def set_state(admin_id: int, state: str) -> bool:
	try:
		await db.execute_query("UPDATE admins SET state = %s WHERE id = %s", (state, admin_id))
		return True
	except Exception as e:
		logger.error(f"Error setting state for admin {admin_id}: {e}")
		return False


async def get_state(admin_id: int) -> str:
	res = await db.execute_query("SELECT state FROM admins WHERE id = %s", (admin_id,))
	return res[0][0] if res else "menu"
