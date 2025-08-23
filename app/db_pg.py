from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import psycopg


def get_conn() -> psycopg.Connection:  # type: ignore[name-defined]
    """Create a new PostgreSQL connection from environment variables.

    Env vars used (with sensible defaults for Docker compose):
      - PGHOST (default: localhost)
      - PGPORT (default: 5432)
      - PGUSER (default: postgres)
      - PGPASSWORD (default: postgres)
      - PGDATABASE (default: legal_case_management)
    """
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    dbname = os.getenv("PGDATABASE", "legal_case_management")

    conn = psycopg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
        autocommit=True,
    )
    return conn


def fetch_all_dicts(cur: psycopg.Cursor, query: str, params: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:  # type: ignore[name-defined]
    cur.execute(query, params or [])
    cols = [d.name for d in cur.description]  # type: ignore[attr-defined]
    out: List[Dict[str, Any]] = []
    for row in cur.fetchall():
        out.append({c: v for c, v in zip(cols, row)})
    return out
