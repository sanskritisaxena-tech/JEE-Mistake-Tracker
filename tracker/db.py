"""Database connection helper and schema creation."""
import sqlite3
import os
from flask import g, current_app


def get_db():
    """Get a database connection for the current request."""
    db_path = current_app.config["DATABASE"]
    # For in-memory DB used in tests, keep a single connection on the app to persist across requests
    if db_path == ":memory:":
        if not hasattr(current_app, "_memory_db"):
            conn = sqlite3.connect(
                ":memory:",
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            conn.execute(SCHEMA_SQL)
            conn.commit()
            current_app._memory_db = conn
        return current_app._memory_db

    if "db" not in g:
        # Ensure parent directory exists (handle :memory: case)
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            uri=True if db_path.startswith("file:") else False,
        )
        g.db.row_factory = sqlite3.Row
        # Ensure schema exists for this connection (important for :memory: and for first run)
        g.db.execute(SCHEMA_SQL)
        g.db.commit()
    return g.db


def close_db(e=None):
    """Close the database connection if it exists."""
    # Do not close in-memory test DB here; it is managed on app
    db_path = None
    try:
        db_path = current_app.config.get("DATABASE")
    except Exception:
        pass
    if db_path == ":memory:":
        return
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app=None):
    """Create the mistakes table if it does not exist."""
    # Support calling with app context or standalone
    if app is not None:
        db_path = app.config["DATABASE"]
    else:
        from config import Config
        db_path = Config.DATABASE
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def init_db_for_connection(conn):
    """Create schema on a given connection (useful for tests with :memory:)."""
    conn.execute(SCHEMA_SQL)
    conn.commit()


SCHEMA_SQL = """
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
"""

# For direct use in tests without Flask app
def get_connection(db_path=":memory:"):
    """Create and return a sqlite3 connection with row_factory set."""
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn
