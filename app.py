"""Entry point for running the app."""
from tracker.app import create_app

app = create_app()

if __name__ == "__main__":
    # Production-safe: debug off by default, allow env override
    import os
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug)
