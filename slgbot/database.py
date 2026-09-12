import aiomysql
import asyncio
import os
from slgbot.logger import logger


def quote_mysql_identifier(identifier: str) -> str:
	if not identifier:
		raise ValueError("MySQL identifier cannot be empty")
	return f"`{identifier.replace('`', '``')}`"


def database_schema_queries(database_name: str) -> list[str]:
	db_name = quote_mysql_identifier(database_name)
	return [
		f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
		f"USE {db_name}",
		*table_schema_queries(),
	]


def table_schema_queries() -> list[str]:
	return [
		"""
		CREATE TABLE IF NOT EXISTS groups (
			id BIGINT NOT NULL PRIMARY KEY,
			name VARCHAR(255) NOT NULL,
			timestp VARCHAR(64) NOT NULL DEFAULT '0',
			has_appeal BOOLEAN NOT NULL DEFAULT FALSE,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
			INDEX idx_groups_has_appeal (has_appeal),
			INDEX idx_groups_name (name)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
		""",
		"""
		CREATE TABLE IF NOT EXISTS admins (
			id BIGINT NOT NULL PRIMARY KEY,
			superadmin BOOLEAN NOT NULL DEFAULT FALSE,
			name VARCHAR(255) NOT NULL DEFAULT '',
			state VARCHAR(64) NOT NULL DEFAULT 'menu',
			dialog TEXT NULL,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
			INDEX idx_admins_superadmin (superadmin)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
		""",
	]


class MySQLDatabase:
	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super(MySQLDatabase, cls).__new__(cls)
		return cls._instance

	def __init__(self):
		if getattr(self, "_inited", False):
			return
		self._inited = True
		self._queue_initialized = False
		self._init_lock = asyncio.Lock()

	async def connect(self):
		if self._queue_initialized:
			return

		async with self._init_lock:
			if self._queue_initialized:
				return

			self.db_host = os.getenv("MYSQL_HOST")
			self.db_port = int(os.getenv("MYSQL_PORT", 3306))
			self.db_user = os.getenv("MYSQL_USER")
			self.db_password = os.getenv("MYSQL_PASSWORD")
			self.db_database = os.getenv("MYSQL_DATABASE")
			queue_size = int(os.getenv("MYSQL_QUEUE_SIZE", 10))

			await self.initialize_database()

			self.connection_queue = asyncio.Queue(maxsize=queue_size)

			for _ in range(queue_size):
				conn = await aiomysql.connect(
					host=self.db_host,
					port=self.db_port,
					user=self.db_user,
					password=self.db_password,
					db=self.db_database,
					autocommit=True
				)
				await self.connection_queue.put(conn)

			self._queue_initialized = True

	async def initialize_database(self):
		if not self.db_database:
			raise ValueError("MYSQL_DATABASE is required")

		await self.ensure_database_exists()

		conn = await aiomysql.connect(
			host=self.db_host,
			port=self.db_port,
			user=self.db_user,
			password=self.db_password,
			db=self.db_database,
			autocommit=True
		)
		try:
			async with conn.cursor() as cur:
				for query in table_schema_queries():
					logger.info(f"Executing database initialization query: {query}")
					await cur.execute(query)
		finally:
			conn.close()
			try:
				await conn.ensure_closed()
			except Exception:
				pass

	async def ensure_database_exists(self):
		conn = await aiomysql.connect(
			host=self.db_host,
			port=self.db_port,
			user=self.db_user,
			password=self.db_password,
			autocommit=True
		)
		try:
			async with conn.cursor() as cur:
				query = database_schema_queries(self.db_database)[0]
				logger.info(f"Executing database initialization query: {query}")
				await cur.execute(query)
		except Exception as e:
			logger.warning(
				f"Could not create database {self.db_database}; continuing with table initialization: {e}"
			)
		finally:
			conn.close()
			try:
				await conn.ensure_closed()
			except Exception:
				pass

	async def connection_reset(self):
		return await aiomysql.connect(
			host=self.db_host,
			port=self.db_port,
			user=self.db_user,
			password=self.db_password,
			db=self.db_database,
			autocommit=True
		)

	async def close(self):
		if not self._queue_initialized:
			return

		while not self.connection_queue.empty():
			conn = await self.connection_queue.get()
			conn.close()
			try:
				await conn.ensure_closed()
			except Exception:
				pass

		self._queue_initialized = False

	async def execute_query(self, query, params=None, as_dict=False, *, max_retries=5):
		if not self._queue_initialized:
			await self.connect()

		last_err = None

		for attempt in range(1, max_retries + 1):
			conn = None
			try:
				try:
					conn = await asyncio.wait_for(self.connection_queue.get(), timeout=10)
				except asyncio.TimeoutError:
					raise RuntimeError("Timeout waiting for a free MySQL connection (queue exhausted)")

				try:
					await conn.ping(reconnect=True)
				except Exception:
					try:
						conn.close()
						await conn.ensure_closed()
					except Exception:
						pass
					conn = await self.connection_reset()

				cursor_type = aiomysql.DictCursor if as_dict else aiomysql.Cursor
				async with conn.cursor(cursor_type) as cur:
					logger.info(f"Executing SQL query: {cur.mogrify(query, params)}")
					await cur.execute(query, params)

					if query.lstrip().upper().startswith("SELECT"):
						return await cur.fetchall()

					return None

			except Exception as e:
				last_err = e
				logger.error(f"Error during executing query: {query}, error: {e}")

				await asyncio.sleep(min(2 * attempt, 15))

			finally:
				if conn is not None:
					try:
						await self.connection_queue.put(conn)
					except Exception:
						try:
							conn.close()
							await conn.ensure_closed()
						except Exception:
							pass

		raise last_err


database = MySQLDatabase()
