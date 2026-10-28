"""Seed script to insert ~60 realistic sample mistakes for preview."""
import os
import random
import datetime
import sqlite3

from tracker.constants import CHAPTERS, ERROR_TYPES, SUBJECTS
from tracker.db import init_db, get_connection
from config import Config

# Optional: load Flask config if available
DB_PATH = Config.DATABASE
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

# Sample test names
TEST_NAMES = [
    "Allen Test 1",
    "Allen Test 2",
    "Allen Test 3",
    "Allen Test 4",
    "Allen Test 5",
    "JEE Main PYQ 2024 Shift 1",
    "JEE Main PYQ 2024 Shift 2",
    "Mock Test 8",
    "FIITJEE AITS 3",
    "Resonance Test 2",
]

SAMPLE_NOTES = [
    "forgot to convert cm to m",
    "missed negative sign",
    "confused between isothermal and adiabatic",
    "formula for range wrong",
    "did not read that g=10 given",
    "silly multiplication error",
    "thought equilibrium constant is concentration",
    "used wrong isomer",
    "forgot limiting reagent",
    "integration constant missed",
    "angle in degrees not radians",
    "misread question asked for magnitude",
    "guessed last 5 mins",
    "time ran out, left blank",
    "vector direction error",
    "",
    "",
    "",
]

def main():
    """Insert about 60 sample mistakes."""
    # Ensure DB exists and schema created
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
    CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT NOT NULL,
        test_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        chapter TEXT NOT NULL,
        error_type TEXT NOT NULL,
        question_ref TEXT,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Clear existing seed? We will just insert; check if already has data
    cur = conn.execute("SELECT COUNT(*) as cnt FROM mistakes")
    cnt = cur.fetchone()["cnt"]
    if cnt > 0:
        print(f"Database already has {cnt} rows, adding more sample data...")

    today = datetime.date.today()
    # Distribute tests over last 90 days
    random.seed(42)
    inserts = 0
    for i in range(60):
        test_name = random.choice(TEST_NAMES)
        # Assign a date per test: group by test_name
        # Create mapping test_name -> date within last 90 days
        # Use deterministic offset based on test index
        idx = TEST_NAMES.index(test_name)
        offset = (idx * 7 + random.randint(0, 6))  # spread 0-70 days ago
        if offset > 90:
            offset = random.randint(0, 90)
        test_date = (today - datetime.timedelta(days=offset)).isoformat()

        subject = random.choice(SUBJECTS)
        chapter = random.choice(CHAPTERS[subject])
        error_type = random.choice(ERROR_TYPES)
        question_ref = f"Q{random.randint(1,30)}"
        note = random.choice(SAMPLE_NOTES)
        if note == "":
            note = None

        conn.execute(
            "INSERT INTO mistakes (test_name, test_date, subject, chapter, error_type, question_ref, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (test_name, test_date, subject, chapter, error_type, question_ref, note),
        )
        inserts += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserts} sample mistakes into {DB_PATH}")

if __name__ == "__main__":
    main()
