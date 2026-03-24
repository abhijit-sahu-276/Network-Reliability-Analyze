from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict


DB_PATH = Path(__file__).resolve().parents[2] / "database" / "network_history.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )
        conn.commit()


def save_analysis(category: str, payload: Dict[str, Any]) -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO analyses (category, payload) VALUES (?, ?)",
            (category, json.dumps(payload)),
        )
        conn.commit()
        return int(cur.lastrowid)


def recent_analyses(limit: int = 20) -> list[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, created_at, category, payload FROM analyses ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out: list[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row[0],
                "created_at": row[1],
                "category": row[2],
                "payload": json.loads(row[3]),
            }
        )
    return out
