from __future__ import annotations

import io
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1]
DB_PATH = APP_DIR / "data" / "chat_history.db"

TITLE_MAX_LEN = 50


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _migrate_legacy_message_columns(con: sqlite3.Connection) -> None:
    """One-time migration: backfill results_json for any pre-multi-chart rows (written only
    to the old single sql/table_json/chart_json columns), then drop those columns - fully
    superseded by results_json since multi-chart support landed. Idempotent: a DB that's
    already migrated (or was never on the old schema) has none of these columns, so this
    is a no-op."""
    existing_columns = {row[1] for row in con.execute("PRAGMA table_info(messages)").fetchall()}
    legacy_columns = {"sql", "table_json", "chart_json"} & existing_columns
    if not legacy_columns:
        return

    rows = con.execute(
        "SELECT id, sql, table_json, chart_json FROM messages "
        "WHERE (results_json IS NULL OR results_json = '') "
        "AND (sql IS NOT NULL OR table_json IS NOT NULL OR chart_json IS NOT NULL)"
    ).fetchall()
    for row_id, sql, table_json, chart_json in rows:
        # table_json/chart_json are already-serialized JSON strings (same shape _serialize_table/
        # _serialize_chart produce) - just wrap them in results_json's outer list-of-blocks shape.
        backfilled = json.dumps([{"sql": sql, "table": table_json, "chart": chart_json}])
        con.execute("UPDATE messages SET results_json = ? WHERE id = ?", (backfilled, row_id))

    for column in ("sql", "table_json", "chart_json"):
        if column in existing_columns:
            con.execute(f"ALTER TABLE messages DROP COLUMN {column}")


def _init_db(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys = ON")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            chat_summary TEXT NOT NULL DEFAULT '',
            summary_upto INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id),
            question TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            answer_kind TEXT NOT NULL,
            answer_icon TEXT NOT NULL,
            results_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Older DBs (before multi-chart support) were created without results_json - add it
    # in place so existing conversation history keeps working.
    existing_columns = {row[1] for row in con.execute("PRAGMA table_info(messages)").fetchall()}
    if "results_json" not in existing_columns:
        con.execute("ALTER TABLE messages ADD COLUMN results_json TEXT")
    _migrate_legacy_message_columns(con)
    con.commit()


_schema_ready = False


def _ensure_schema(con: sqlite3.Connection) -> None:
    """Run _init_db() at most once per process - it only ever needs to create the tables
    and apply the results_json migration the first time, but _connect() is called on
    nearly every rerun (e.g. the floating chatbot popover loads turns on every page), so
    redoing the CREATE TABLE/PRAGMA table_info checks every time was pure waste."""
    global _schema_ready
    if _schema_ready:
        return
    _init_db(con)
    _schema_ready = True


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        _ensure_schema(con)
        yield con
    finally:
        con.close()


def create_conversation() -> int:
    now = _now()
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO conversations (title, created_at, updated_at) VALUES (NULL, ?, ?)",
            (now, now),
        )
        con.commit()
        return int(cur.lastrowid)


def list_conversations() -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [
        {"id": row[0], "title": row[1], "created_at": row[2], "updated_at": row[3]}
        for row in rows
    ]


def get_conversation(conversation_id: int) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute(
            "SELECT id, title, chat_summary, summary_upto FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "title": row[1], "chat_summary": row[2], "summary_upto": row[3]}


def update_title(conversation_id: int, title: str) -> None:
    with _connect() as con:
        con.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
        con.commit()


def update_summary(conversation_id: int, summary: str, summary_upto: int) -> None:
    with _connect() as con:
        con.execute(
            "UPDATE conversations SET chat_summary = ?, summary_upto = ? WHERE id = ?",
            (summary, summary_upto, conversation_id),
        )
        con.commit()


def _serialize_table(table: pd.DataFrame | None) -> str | None:
    if table is None:
        return None
    return table.to_json(orient="records")


def _deserialize_table(raw: str | None) -> pd.DataFrame | None:
    if not raw:
        return None
    return pd.read_json(io.StringIO(raw), orient="records")


def _serialize_chart(chart: Any | None) -> str | None:
    if chart is None:
        return None
    return chart.to_json()


def _deserialize_chart(raw: str | None) -> Any | None:
    if not raw:
        return None
    import plotly.io as pio

    return pio.from_json(raw)


def _serialize_results(results: list[dict[str, Any]]) -> str:
    return json.dumps(
        [
            {
                "sql": block.get("sql"),
                "table": _serialize_table(block.get("table")),
                "chart": _serialize_chart(block.get("chart")),
                "total_rows": block.get("total_rows"),
            }
            for block in results
        ]
    )


def _deserialize_results(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    return [
        {
            "sql": block.get("sql"),
            "table": _deserialize_table(block.get("table")),
            "chart": _deserialize_chart(block.get("chart")),
            # Older rows saved before this field existed - None means "unknown", not
            # "not truncated", so render_turn's export button only offers itself when it
            # can positively confirm more rows exist.
            "total_rows": block.get("total_rows"),
        }
        for block in json.loads(raw)
    ]


def append_turn(conversation_id: int, question: str, response: dict[str, Any], answer_icon: str) -> None:
    now = _now()
    with _connect() as con:
        con.execute(
            """
            INSERT INTO messages
                (conversation_id, question, answer_text, answer_kind, answer_icon, results_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                question,
                response.get("text") or "",
                response.get("kind") or "",
                answer_icon,
                _serialize_results(response.get("results") or []),
                now,
            ),
        )
        row = con.execute(
            "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        title = row[0] if row else None
        if not title:
            title = question.strip()[:TITLE_MAX_LEN]
            if len(question.strip()) > TITLE_MAX_LEN:
                title += "…"
        con.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conversation_id),
        )
        con.commit()


def load_turns(conversation_id: int | None) -> list[tuple[str, dict[str, Any], str, str]]:
    if conversation_id is None:
        return []
    with _connect() as con:
        rows = con.execute(
            """
            SELECT question, answer_text, answer_kind, results_json, answer_icon, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
    turns = []
    for question, answer_text, answer_kind, results_json, answer_icon, created_at in rows:
        response = {"kind": answer_kind, "text": answer_text, "results": _deserialize_results(results_json)}
        turns.append((question, response, answer_icon, created_at))
    return turns


def delete_conversation(conversation_id: int) -> None:
    with _connect() as con:
        con.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        con.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        con.commit()
