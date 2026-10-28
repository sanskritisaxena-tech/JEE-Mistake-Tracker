"""Application configuration."""
import os


class Config:
    """Base configuration."""

    # Database path configurable via environment variable, defaults to ./data/tracker.db
    DATABASE = os.environ.get("TRACKER_DB", os.path.join(os.path.dirname(__file__), "data", "tracker.db"))
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    # CSRF enabled
    WTF_CSRF_ENABLED = True
