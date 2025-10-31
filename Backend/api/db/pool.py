from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from .config import DATABASE_URL

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        # Default to UTC in DB; application will write Asia/Bangkok timestamps
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            kwargs={"autocommit": True},
            min_size=1,
            max_size=int(os.getenv("DB_POOL_MAX", "10")),
            timeout=30,
        )
    return _pool


@contextmanager
def get_conn():
    pool = get_pool()
    with pool.connection() as conn:
        # Use dict_row for convenience
        conn.row_factory = dict_row
        # Ensure timezone session (for timestamptz rendering)
        with conn.cursor() as cur:
            cur.execute("SET TIME ZONE 'Asia/Bangkok'")
        yield conn
