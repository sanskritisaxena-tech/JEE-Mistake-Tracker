"""Tests for query functions using in-memory SQLite."""
import sqlite3
import datetime
import pytest

from tracker.db import init_db_for_connection, get_connection
from tracker import queries


@pytest.fixture
def conn():
    """Create an in-memory DB with schema."""
    conn = get_connection(":memory:")
    init_db_for_connection(conn)
    yield conn
    conn.close()


def seed_sample(conn):
    """Insert sample data for tests."""
    today = datetime.date.today()
    # Use dates within last 90 days
    def d(offset):
        return (today - datetime.timedelta(days=offset)).isoformat()

    data = [
        ("Mock 1", d(5), "Physics", "Kinematics", "Concept gap", "Q1", "note1"),
        ("Mock 1", d(5), "Physics", "Kinematics", "Calculation slip", "Q2", ""),
        ("Mock 1", d(5), "Chemistry", "Atomic Structure", "Concept gap", "Q3", ""),
        ("Mock 2", d(10), "Mathematics", "Coordinate Geometry", "Misread question", "Q4", ""),
        ("Mock 2", d(10), "Physics", "Kinematics", "Concept gap", "Q5", ""),
        ("Mock 3", d(20), "Chemistry", "Equilibrium", "Formula not remembered", "Q6", ""),
        ("Mock 3", d(40), "Mathematics", "Integral Calculus", "Time pressure", "Q7", ""),
        ("Old Test", d(100), "Physics", "Optics", "Guessed", "Q8", ""),
    ]
    for row in data:
        queries.insert_mistake(conn, *row)


def test_stats_by_subject(conn):
    """Test stats by subject counts correctly."""
    seed_sample(conn)
    stats = queries.get_stats_by_subject(conn)
    # Convert to dict
    d = {r["subject"]: r["count"] for r in stats}
    assert d["Physics"] == 4  # Kinematics 3 + Optics 1
    assert d["Chemistry"] == 2
    assert d["Mathematics"] == 2


def test_stats_by_subject_date_filter(conn):
    """Test date-range filtering for subject stats."""
    seed_sample(conn)
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=14)).isoformat()
    end = today.isoformat()
    stats = queries.get_stats_by_subject(conn, start_date=start, end_date=end)
    d = {r["subject"]: r["count"] for r in stats}
    # Within 14 days: Mock1 (5d) 3 entries + Mock2 (10d) 2 entries = 5
    # Mock1: Physics 2, Chemistry 1 ; Mock2: Mathematics 1, Physics 1
    assert d.get("Physics") == 3
    assert d.get("Chemistry") == 1
    assert d.get("Mathematics") == 1
    total = sum(d.values())
    assert total == 5


def test_stats_by_error_type(conn):
    """Test stats by error type."""
    seed_sample(conn)
    stats = queries.get_stats_by_error_type(conn)
    d = {r["error_type"]: r["count"] for r in stats}
    assert d["Concept gap"] == 3
    assert d["Calculation slip"] == 1
    assert d["Time pressure"] == 1


def test_top_chapters(conn):
    """Test top chapters ranking."""
    seed_sample(conn)
    top = queries.get_top_chapters(conn, limit=5)
    assert len(top) == 5
    # Kinematics should be top with 3
    assert top[0]["chapter"] == "Kinematics"
    assert top[0]["count"] == 3


def test_revision_ranking(conn):
    """Test revision ranking returns chapters sorted by count with most common error type."""
    seed_sample(conn)
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=28)).isoformat()
    end = today.isoformat()
    ranking = queries.get_revision_ranking(conn, start_date=start, end_date=end, limit=10)
    # Within 28 days: exclude 40d and 100d entries
    # So we have 6 entries: Mock1 3 + Mock2 2 + Mock3 1 (20d)
    assert len(ranking) == 4  # Kinematics, Atomic Structure, Coordinate Geometry, Equilibrium
    # Kinematics top
    assert ranking[0]["chapter"] == "Kinematics"
    assert ranking[0]["count"] == 3
    assert ranking[0]["most_common_error_type"] == "Concept gap"


def test_date_range_filtering(conn):
    """Test date filtering for total and for per-test counts."""
    seed_sample(conn)
    today = datetime.date.today()
    start_all = (today - datetime.timedelta(days=90)).isoformat()
    start_recent = (today - datetime.timedelta(days=15)).isoformat()
    end = today.isoformat()

    total_all = queries.get_total_in_range(conn, start_date=start_all, end_date=end)
    # 90 day window excludes 100d entry => 7 entries
    assert total_all == 7

    total_recent = queries.get_total_in_range(conn, start_date=start_recent, end_date=end)
    # 15 day window: Mock1 (5d) 3 + Mock2 (10d) 2 =5
    assert total_recent == 5

    per_test = queries.get_mistakes_per_test(conn, start_date=start_recent, end_date=end)
    # Should have Mock1 and Mock2
    names = {r["test_name"] for r in per_test}
    assert "Mock 1" in names
    assert "Mock 2" in names
    assert "Old Test" not in names


def test_mistakes_per_test_all_time(conn):
    """Test per-test grouping."""
    seed_sample(conn)
    per_test = queries.get_mistakes_per_test(conn)
    assert len(per_test) == 5  # Mock1, Mock2, Mock3 has 2 dates, Old Test
    # Check that Mock 1 group exists with count 3
    mock1 = [r for r in per_test if r["test_name"] == "Mock 1"]
    assert len(mock1) == 1
    assert mock1[0]["count"] == 3


def test_revision_empty(conn):
    """Empty DB returns empty ranking."""
    ranking = queries.get_revision_ranking(conn)
    assert ranking == []
    stats = queries.get_stats_by_subject(conn)
    assert stats == []


def test_filtered_list_and_count(conn):
    """Test list_mistakes filtering."""
    seed_sample(conn)
    rows = queries.list_mistakes(conn, subject="Physics")
    assert len(rows) == 4
    cnt = queries.count_filtered(conn, subject="Physics")
    assert cnt == 4

# Additional checks
def test_most_error_prone_subject(conn):
    seed_sample(conn)
    assert queries.get_most_error_prone_subject(conn) == "Physics"

def test_most_common_error_type(conn):
    seed_sample(conn)
    assert queries.get_most_common_error_type(conn) == "Concept gap"

def test_most_error_prone_none(conn):
    assert queries.get_most_error_prone_subject(conn) is None
    assert queries.get_most_common_error_type(conn) is None
