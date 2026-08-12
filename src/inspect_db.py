import sys
from pathlib import Path

#Add project root directory to Python path dynamically
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import sqlite3
from src.config import Config

def inspect_database():
    """Reads and displays stored conversation turns from the SQLite database"""
    db_path = Config.DB_PATH

    if not db_path.exists():
        print(f"Database file not found at: {db_path}")
        return

    print(f"=== Inspecting SQLite Database: {db_path.name} ===\n")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #Query total messages
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    total_messages = cursor.fetchone()["total"]
    print(f"Total Messages Persisted: {total_messages}\n" + "-" * 50)

    #Fetch all stored records
    cursor.execute("""
        SELECT id, session_id, role, content, timestamp
        FROM messages
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()

    for row in rows:
        role_icon = "👤" if row["role"] == "user" else "🛡️"
        print(f"[{row['id']} [{row['timestamp']} Session: {row['session_id']}")
        print(f"{role_icon} Role: {row['role'].upper()}")
        print(f"Content:\n{row['content']}")
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    inspect_database()