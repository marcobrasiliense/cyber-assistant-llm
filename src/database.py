import sqlite3
from pathlib import Path
from typing import List, Dict, Any


class DatabaseManager:
    """Manages SQLite persistence for chat history and user conversations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection instance to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enables access to columns by name
        return conn

    def _init_db(self) -> None:
        """Creates table schema if it does not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS messages
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               session_id
                               TEXT
                               NOT
                               NULL,
                               role
                               TEXT
                               NOT
                               NULL,
                               content
                               TEXT
                               NOT
                               NULL,
                               timestamp
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           """)
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Persists a new message turn (user or assistant) into the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()

    def get_recent_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieves the last N messages for a session to construct a token-efficient context window.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT role, content
                           FROM (SELECT role, content, id
                                 FROM messages
                                 WHERE session_id = ?
                                 ORDER BY id DESC LIMIT ?) AS subquery
                           ORDER BY id ASC
                           """, (session_id, limit))

            rows = cursor.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

    def clear_session(self, session_id: str) -> None:
        """Clears stored history for a given session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()