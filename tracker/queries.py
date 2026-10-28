"""All SQL and statistics functions. Each function has a docstring."""
import sqlite3


def insert_mistake(conn, test_name, test_date, subject, chapter, error_type, question_ref=None, note=None):
    """Insert a new mistake and return its id."""
    cur = conn.execute(
        """
        INSERT INTO mistakes (test_name, test_date, subject, chapter, error_type, question_ref, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (test_name, test_date, subject, chapter, error_type, question_ref, note),
    )
    conn.commit()
    return cur.lastrowid


def get_mistake_by_id(conn, mistake_id):
    """Fetch a single mistake by id, or None."""
    cur = conn.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,))
    return cur.fetchone()


def update_mistake(conn, mistake_id, test_name, test_date, subject, chapter, error_type, question_ref=None, note=None):
    """Update an existing mistake."""
    conn.execute(
        """
        UPDATE mistakes
        SET test_name = ?, test_date = ?, subject = ?, chapter = ?, error_type = ?, question_ref = ?, note = ?
        WHERE id = ?
        """,
        (test_name, test_date, subject, chapter, error_type, question_ref, note, mistake_id),
    )
    conn.commit()


def delete_mistake(conn, mistake_id):
    """Delete a mistake by id."""
    conn.execute("DELETE FROM mistakes WHERE id = ?", (mistake_id,))
    conn.commit()


def count_mistakes_for_test(conn, test_name):
    """Count how many mistakes are logged for a given test_name."""
    cur = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE test_name = ?", (test_name,))
    row = cur.fetchone()
    return row["cnt"] if row else 0


def list_mistakes(conn, subject=None, chapter=None, error_type=None, test_name=None, limit=50, offset=0):
    """List mistakes with optional filters, newest first.

    Filters combine with AND. Supports pagination via limit/offset.
    """
    query = "SELECT * FROM mistakes WHERE 1=1"
    params = []

    if subject:
        query += " AND subject = ?"
        params.append(subject)
    if chapter:
        query += " AND chapter = ?"
        params.append(chapter)
    if error_type:
        query += " AND error_type = ?"
        params.append(error_type)
    if test_name:
        query += " AND test_name = ?"
        params.append(test_name)

    query += " ORDER BY test_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur = conn.execute(query, params)
    return cur.fetchall()


def count_filtered(conn, subject=None, chapter=None, error_type=None, test_name=None):
    """Count mistakes matching the given filters."""
    query = "SELECT COUNT(*) as cnt FROM mistakes WHERE 1=1"
    params = []
    if subject:
        query += " AND subject = ?"
        params.append(subject)
    if chapter:
        query += " AND chapter = ?"
        params.append(chapter)
    if error_type:
        query += " AND error_type = ?"
        params.append(error_type)
    if test_name:
        query += " AND test_name = ?"
        params.append(test_name)
    cur = conn.execute(query, params)
    row = cur.fetchone()
    return row["cnt"] if row else 0


def distinct_test_names(conn):
    """Return distinct test names ordered alphabetically."""
    cur = conn.execute("SELECT DISTINCT test_name FROM mistakes ORDER BY test_name")
    return [r["test_name"] for r in cur.fetchall()]


def get_stats_by_subject(conn, start_date=None, end_date=None):
    """Return mistake counts grouped by subject for the date range.

    If start_date/end_date are None, includes all time.
    Returns list of dicts: {subject, count}
    """
    query = "SELECT subject, COUNT(*) as count FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " GROUP BY subject ORDER BY count DESC"
    cur = conn.execute(query, params)
    rows = cur.fetchall()
    return [{"subject": r["subject"], "count": r["count"]} for r in rows]


def get_stats_by_error_type(conn, start_date=None, end_date=None):
    """Return mistake counts grouped by error_type for the date range.

    Returns list of dicts: {error_type, count}
    """
    query = "SELECT error_type, COUNT(*) as count FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " GROUP BY error_type ORDER BY count DESC"
    cur = conn.execute(query, params)
    rows = cur.fetchall()
    return [{"error_type": r["error_type"], "count": r["count"]} for r in rows]


def get_top_chapters(conn, start_date=None, end_date=None, limit=5):
    """Return top chapters by mistake count.

    Returns list of dicts: {chapter, subject, count}
    """
    query = "SELECT chapter, subject, COUNT(*) as count FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " GROUP BY chapter, subject ORDER BY count DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    rows = cur.fetchall()
    return [{"chapter": r["chapter"], "subject": r["subject"], "count": r["count"]} for r in rows]


def get_mistakes_per_test(conn, start_date=None, end_date=None):
    """Return mistake counts per test grouped by test_name and test_date.

    Returns list of dicts: {test_name, test_date, count} ordered by test_date.
    """
    query = "SELECT test_name, test_date, COUNT(*) as count FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " GROUP BY test_name, test_date ORDER BY test_date ASC"
    cur = conn.execute(query, params)
    rows = cur.fetchall()
    return [{"test_name": r["test_name"], "test_date": r["test_date"], "count": r["count"]} for r in rows]


def get_total_in_range(conn, start_date=None, end_date=None):
    """Return total mistake count in the date range."""
    query = "SELECT COUNT(*) as cnt FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    cur = conn.execute(query, params)
    row = cur.fetchone()
    return row["cnt"] if row else 0


def get_most_error_prone_subject(conn, start_date=None, end_date=None):
    """Return the subject with the highest mistake count, or None if no data."""
    stats = get_stats_by_subject(conn, start_date, end_date)
    if not stats:
        return None
    return stats[0]["subject"]


def get_most_common_error_type(conn, start_date=None, end_date=None):
    """Return the most common error_type, or None if no data."""
    stats = get_stats_by_error_type(conn, start_date, end_date)
    if not stats:
        return None
    return stats[0]["error_type"]


def get_revision_ranking(conn, start_date=None, end_date=None, limit=10):
    """Rank chapters by mistake count in the window.

    For each chapter returns: subject, chapter, count, most_common_error_type
    """
    # First get the top chapters
    query = "SELECT chapter, subject, COUNT(*) as count FROM mistakes WHERE 1=1"
    params = []
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " GROUP BY chapter, subject ORDER BY count DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    top = cur.fetchall()

    result = []
    for row in top:
        chapter = row["chapter"]
        subject = row["subject"]
        count = row["count"]
        # Most common error type for this chapter in the window
        q2 = "SELECT error_type, COUNT(*) as cnt FROM mistakes WHERE chapter = ? AND subject = ?"
        p2 = [chapter, subject]
        if start_date:
            q2 += " AND test_date >= ?"
            p2.append(start_date)
        if end_date:
            q2 += " AND test_date <= ?"
            p2.append(end_date)
        q2 += " GROUP BY error_type ORDER BY cnt DESC LIMIT 1"
        cur2 = conn.execute(q2, p2)
        er = cur2.fetchone()
        most_common = er["error_type"] if er else None
        result.append(
            {
                "chapter": chapter,
                "subject": subject,
                "count": count,
                "most_common_error_type": most_common,
            }
        )
    return result


def get_notes_for_chapter(conn, chapter, subject, start_date=None, end_date=None):
    """Return notes for a given chapter/subject in the window, newest first."""
    query = "SELECT note, question_ref, test_name, test_date, error_type FROM mistakes WHERE chapter = ? AND subject = ?"
    params = [chapter, subject]
    if start_date:
        query += " AND test_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND test_date <= ?"
        params.append(end_date)
    query += " ORDER BY test_date DESC, id DESC"
    cur = conn.execute(query, params)
    return cur.fetchall()


def get_all_for_export(conn, subject=None, chapter=None, error_type=None, test_name=None):
    """Return all matching rows for CSV export (no pagination)."""
    query = "SELECT * FROM mistakes WHERE 1=1"
    params = []
    if subject:
        query += " AND subject = ?"
        params.append(subject)
    if chapter:
        query += " AND chapter = ?"
        params.append(chapter)
    if error_type:
        query += " AND error_type = ?"
        params.append(error_type)
    if test_name:
        query += " AND test_name = ?"
        params.append(test_name)
    query += " ORDER BY test_date DESC, id DESC"
    cur = conn.execute(query, params)
    return cur.fetchall()
