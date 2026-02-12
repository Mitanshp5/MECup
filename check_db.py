import sqlite3
import os

DB_PATH = "mecup.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} does not exist.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"Checking integrity of {DB_PATH}...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchall()
        print(f"Integrity check result: {result}")
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_db()
