# JEE Mistake Tracker

A quiet, personal study tool for a JEE aspirant to log questions she got wrong in mock tests, see patterns in her mistakes, and get a focused revision list.

## What the app is

After a mock test, you log each wrong or skipped question with a few tags: test name, date, subject, chapter, error type, and an optional note. The app shows where marks are being lost and ranks chapters to revise first. No accounts, no sharing, just a local tracker.

## How to install and run

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

The database path is configurable via the `TRACKER_DB` environment variable. By default it uses `./data/tracker.db` (the `data/` directory is created automatically).

To use a different database:

```bash
TRACKER_DB=/path/to/my.db python app.py
```

For production deployment, set a strong `SECRET_KEY` environment variable:

```bash
SECRET_KEY=your-secret python app.py
```

Debug mode is off by default. Enable with `FLASK_DEBUG=1` only for local development.

A `Procfile` is included for platforms like Heroku or Render:

```
web: gunicorn 'tracker.app:create_app()'
```

Install gunicorn in that environment if needed (`pip install gunicorn`).

## How to run the tests

```bash
pytest
```

Tests use an in-memory SQLite database and cover the statistics and query functions.

## Project structure

```
tracker/
  app.py              # app factory and routes
  db.py               # connection helper, schema creation
  queries.py          # all SQL and stats functions
  constants.py        # subjects, error types, chapter lists
  templates/          # base.html, add.html, list.html, dashboard.html, revision.html, edit.html
  static/css/style.css
  static/js/theme.js, charts.js, form.js
  static/vendor/chart.umd.js
  tests/test_queries.py
config.py             # database path and secret key
seed.py               # optional sample data
requirements.txt
README.md
```

## How it works

1. Browser sends a request to a Flask route in `tracker/app.py`.
2. The route validates input and calls a query function in `tracker/queries.py`.
3. The query function runs parameterized SQL against SQLite via the helper in `tracker/db.py`.
4. The route renders a Jinja template, which includes plain CSS and vanilla JavaScript.
5. The response is sent back to the browser. No ORM, no build step, no framework on the frontend.

Forms use server-side validation and CSRF tokens. The dashboard and revision pages compute date-window aggregates in SQL and render results with text summaries and Chart.js bar and line charts.

To preview the app with sample data:

```bash
python seed.py
```

This inserts about 60 realistic mistakes across several mock tests. It never runs automatically and can be run multiple times.

## What I learned

