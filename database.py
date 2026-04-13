"""
Async SQLite database with connection pooling and indexes
"""
import asyncio
import logging
from typing import Optional
import aiosqlite

from config import DB_PATH, DB_POOL_SIZE, ALL_CATEGORIES, DEFAULT_LANGUAGE, DEFAULT_INTERVAL

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=DB_POOL_SIZE)
        self._connections = []

    async def init(self):
        for _ in range(DB_POOL_SIZE):
            conn = await aiosqlite.connect(DB_PATH)
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=10000")
            await conn.execute("PRAGMA temp_store=MEMORY")
            self._connections.append(conn)
            await self._pool.put(conn)
        await self._create_tables()
        logger.info(f"DB pool initialized with {DB_POOL_SIZE} connections")

    async def _get(self):
        return await asyncio.wait_for(self._pool.get(), timeout=5.0)

    async def _put(self, conn):
        await self._pool.put(conn)

    async def _create_tables(self):
        conn = await self._get()
        try:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id   INTEGER PRIMARY KEY,
                    username  TEXT,
                    language  TEXT NOT NULL DEFAULT 'ru',
                    interval  INTEGER NOT NULL DEFAULT 0,
                    last_sent INTEGER NOT NULL DEFAULT 0,
                    active    INTEGER NOT NULL DEFAULT 1,
                    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                );
                CREATE TABLE IF NOT EXISTS user_categories (
                    user_id  INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    enabled  INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (user_id, category),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_users_sched ON users(interval, last_sent, active);
                CREATE INDEX IF NOT EXISTS idx_uc_user ON user_categories(user_id);
                CREATE INDEX IF NOT EXISTS idx_uc_enabled ON user_categories(user_id, enabled);
            """)
            await conn.commit()
        finally:
            await self._put(conn)

    async def get_or_create_user(self, user_id: int, username: str = "") -> dict:
        conn = await self._get()
        try:
            async with conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
                row = await cur.fetchone()
            if row:
                return dict(row)
            await conn.execute(
                "INSERT OR IGNORE INTO users (user_id,username,language,interval,last_sent) VALUES (?,?,?,?,0)",
                (user_id, username, DEFAULT_LANGUAGE, DEFAULT_INTERVAL),
            )
            await conn.commit()
            async with conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
                return dict(await cur.fetchone())
        finally:
            await self._put(conn)

    async def get_user(self, user_id: int) -> Optional[dict]:
        conn = await self._get()
        try:
            async with conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None
        finally:
            await self._put(conn)

    async def set_language(self, user_id: int, language: str):
        """Установить язык пользователя"""
        conn = await self._get()
        try:
            await conn.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))
            await conn.commit()
            logger.info(f"Language for user {user_id} set to {language}")
        except Exception as e:
            logger.error(f"Set language error: {e}")
        finally:
            await self._put(conn)

    async def set_interval(self, user_id: int, interval: int):
        conn = await self._get()
        try:
            await conn.execute(
                "UPDATE users SET interval=?, active=? WHERE user_id=?",
                (interval, 1 if interval > 0 else 0, user_id),
            )
            await conn.commit()
        finally:
            await self._put(conn)

    async def disable_user(self, user_id: int):
        conn = await self._get()
        try:
            await conn.execute("UPDATE users SET active=0,interval=0 WHERE user_id=?", (user_id,))
            await conn.commit()
        finally:
            await self._put(conn)

    async def update_last_sent(self, user_id: int, ts: int):
        conn = await self._get()
        try:
            await conn.execute("UPDATE users SET last_sent=? WHERE user_id=?", (ts, user_id))
            await conn.commit()
        finally:
            await self._put(conn)

    async def get_user_categories(self, user_id: int) -> set:
        conn = await self._get()
        try:
            async with conn.execute(
                "SELECT category FROM user_categories WHERE user_id=? AND enabled=1", (user_id,)
            ) as cur:
                return {r[0] for r in await cur.fetchall()}
        finally:
            await self._put(conn)

    async def toggle_category(self, user_id: int, category: str) -> bool:
        conn = await self._get()
        try:
            async with conn.execute(
                "SELECT enabled FROM user_categories WHERE user_id=? AND category=?", (user_id, category)
            ) as cur:
                row = await cur.fetchone()
            if row:
                new = 0 if row[0] else 1
                await conn.execute(
                    "UPDATE user_categories SET enabled=? WHERE user_id=? AND category=?",
                    (new, user_id, category),
                )
            else:
                new = 1
                await conn.execute(
                    "INSERT INTO user_categories (user_id,category,enabled) VALUES (?,?,1)", (user_id, category)
                )
            await conn.commit()
            return bool(new)
        finally:
            await self._put(conn)

    async def set_group_categories(self, user_id: int, group_key: str, enabled: bool):
        conn = await self._get()
        try:
            cats = list(ALL_CATEGORIES[group_key]["items"].keys())
            val = 1 if enabled else 0
            await conn.executemany(
                "INSERT INTO user_categories (user_id,category,enabled) VALUES (?,?,?) "
                "ON CONFLICT(user_id,category) DO UPDATE SET enabled=excluded.enabled",
                [(user_id, c, val) for c in cats],
            )
            await conn.commit()
        finally:
            await self._put(conn)

    async def set_all_categories(self, user_id: int, enabled: bool):
        conn = await self._get()
        try:
            all_cats = [c for g in ALL_CATEGORIES.values() for c in g["items"]]
            val = 1 if enabled else 0
            await conn.executemany(
                "INSERT INTO user_categories (user_id,category,enabled) VALUES (?,?,?) "
                "ON CONFLICT(user_id,category) DO UPDATE SET enabled=excluded.enabled",
                [(user_id, c, val) for c in all_cats],
            )
            await conn.commit()
        finally:
            await self._put(conn)

    async def get_users_to_notify(self, now: int) -> list:
        conn = await self._get()
        try:
            async with conn.execute(
                """SELECT user_id,language,interval,last_sent FROM users
                   WHERE active=1 AND interval>0 AND (last_sent + interval*3600) <= ?""",
                (now,),
            ) as cur:
                return [dict(r) for r in await cur.fetchall()]
        finally:
            await self._put(conn)

    async def close(self):
        for conn in self._connections:
            await conn.close()