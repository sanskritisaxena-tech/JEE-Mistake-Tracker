"""Flask application factory and routes."""
import os
import csv
import io
import datetime
import secrets
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    Response,
    g,
    current_app,
)
from tracker.db import get_db, close_db, init_db
from tracker import queries
from tracker.constants import SUBJECTS, ERROR_TYPES, CHAPTERS, is_valid_chapter_for_subject


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load config
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)

    # Ensure secret key
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(16)

    # Init DB if not in testing with :memory:
    if app.config["DATABASE"] != ":memory:":
        # Ensure directory exists and create tables
        init_db(app)

    app.teardown_appcontext(close_db)

    # CSRF helpers
    @app.before_request
    def csrf_protect():
        """Simple CSRF protection."""
        if request.method == "POST":
            token = session.get("csrf_token")
            form_token = request.form.get("csrf_token")
            if not token or not form_token or token != form_token:
                # For API JSON? Just abort
                return "CSRF token missing or invalid", 400

    @app.context_processor
    def inject_csrf():
        """Inject csrf_token into templates."""
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return dict(csrf_token=session["csrf_token"])

    # Helper validation
    def validate_mistake_form(form):
        """Validate form data, return (errors dict, cleaned data)."""
        errors = {}
        test_name = form.get("test_name", "").strip()
        test_date = form.get("test_date", "").strip()
        subject = form.get("subject", "").strip()
        chapter = form.get("chapter", "").strip()
        error_type = form.get("error_type", "").strip()
        question_ref = form.get("question_ref", "").strip()
        note = form.get("note", "").strip()

        if not test_name:
            errors["test_name"] = "Test name is required."
        if not test_date:
            errors["test_date"] = "Test date is required."
        else:
            try:
                datetime.date.fromisoformat(test_date)
            except ValueError:
                errors["test_date"] = "Invalid date format."

        if not subject:
            errors["subject"] = "Subject is required."
        elif subject not in SUBJECTS:
            errors["subject"] = "Invalid subject."

        if not chapter:
            errors["chapter"] = "Chapter is required."
        elif subject and chapter:
            if not is_valid_chapter_for_subject(subject, chapter):
                errors["chapter"] = "Chapter does not belong to the selected subject."

        if not error_type:
            errors["error_type"] = "Error type is required."
        elif error_type not in ERROR_TYPES:
            errors["error_type"] = "Invalid error type."

        if note and len(note) > 300:
            errors["note"] = "Note must be 300 characters or fewer."

        cleaned = {
            "test_name": test_name,
            "test_date": test_date,
            "subject": subject,
            "chapter": chapter,
            "error_type": error_type,
            "question_ref": question_ref or None,
            "note": note or None,
        }
        return errors, cleaned

    # Routes
    @app.route("/", methods=["GET", "POST"])
    def add_mistake():
        """Home page: add mistake form."""
        db = get_db()
        message = None
        # Preserve form values after POST for re-render
        form_data = {}
        errors = {}

        if request.method == "POST":
            errors, cleaned = validate_mistake_form(request.form)
            form_data = cleaned
            # Keep raw values for re-display if errors
            if not errors:
                queries.insert_mistake(
                    db,
                    cleaned["test_name"],
                    cleaned["test_date"],
                    cleaned["subject"],
                    cleaned["chapter"],
                    cleaned["error_type"],
                    cleaned["question_ref"],
                    cleaned["note"],
                )
                count = queries.count_mistakes_for_test(db, cleaned["test_name"])
                # Success: render form again with retained fields
                # After saving, clear only question_ref and note, keep test_name, date, subject
                message = f"Saved. {count} logged for this test."
                # Prepare form_data for next entry: keep test_name, test_date, subject, chapter, error_type
                # Clear question_ref and note
                form_data["question_ref"] = ""
                form_data["note"] = ""
                # Don't show errors
                errors = {}
            else:
                # Re-populate with submitted values
                form_data = {
                    "test_name": request.form.get("test_name", ""),
                    "test_date": request.form.get("test_date", ""),
                    "subject": request.form.get("subject", ""),
                    "chapter": request.form.get("chapter", ""),
                    "error_type": request.form.get("error_type", ""),
                    "question_ref": request.form.get("question_ref", ""),
                    "note": request.form.get("note", ""),
                }
        else:
            # GET: default date today
            form_data = {
                "test_name": request.args.get("test_name", ""),
                "test_date": datetime.date.today().isoformat(),
                "subject": request.args.get("subject", ""),
                "chapter": "",
                "error_type": "",
                "question_ref": "",
                "note": "",
            }
            # Allow pre-fill via query but ensure date default
            if not form_data["test_date"]:
                form_data["test_date"] = datetime.date.today().isoformat()

        return render_template(
            "add.html",
            subjects=SUBJECTS,
            error_types=ERROR_TYPES,
            chapters=CHAPTERS,
            form_data=form_data,
            errors=errors,
            message=message,
        )

    @app.route("/mistakes")
    def list_mistakes():
        """Mistake list with filters."""
        db = get_db()
        subject = request.args.get("subject", "").strip() or None
        chapter = request.args.get("chapter", "").strip() or None
        error_type = request.args.get("error_type", "").strip() or None
        test_name = request.args.get("test_name", "").strip() or None

        # Pagination: page param, 50 per page
        try:
            page = int(request.args.get("page", "1"))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        limit = 50
        offset = (page - 1) * limit

        # Fetch one extra to know if there's more
        rows = queries.list_mistakes(db, subject=subject, chapter=chapter, error_type=error_type, test_name=test_name, limit=limit+1, offset=offset)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        total = queries.count_filtered(db, subject=subject, chapter=chapter, error_type=error_type, test_name=test_name)
        # For filters dropdown, get distinct test names
        test_names = queries.distinct_test_names(db)

        # Determine if load more should show next page number
        next_page = page + 1 if has_more else None

        return render_template(
            "list.html",
            mistakes=rows,
            total=total,
            has_more=has_more,
            next_page=next_page,
            page=page,
            subjects=SUBJECTS,
            error_types=ERROR_TYPES,
            chapters=CHAPTERS,
            test_names=test_names,
            filters={
                "subject": subject or "",
                "chapter": chapter or "",
                "error_type": error_type or "",
                "test_name": test_name or "",
            },
        )

    @app.route("/mistakes/<int:mid>/edit", methods=["GET", "POST"])
    def edit_mistake(mid):
        """Edit a mistake."""
        db = get_db()
        mistake = queries.get_mistake_by_id(db, mid)
        if not mistake:
            return "Not found", 404

        if request.method == "POST":
            errors, cleaned = validate_mistake_form(request.form)
            if not errors:
                queries.update_mistake(
                    db,
                    mid,
                    cleaned["test_name"],
                    cleaned["test_date"],
                    cleaned["subject"],
                    cleaned["chapter"],
                    cleaned["error_type"],
                    cleaned["question_ref"],
                    cleaned["note"],
                )
                return redirect(url_for("list_mistakes"))
            else:
                form_data = {
                    "test_name": request.form.get("test_name", ""),
                    "test_date": request.form.get("test_date", ""),
                    "subject": request.form.get("subject", ""),
                    "chapter": request.form.get("chapter", ""),
                    "error_type": request.form.get("error_type", ""),
                    "question_ref": request.form.get("question_ref", ""),
                    "note": request.form.get("note", ""),
                }
                return render_template(
                    "edit.html",
                    mistake=mistake,
                    subjects=SUBJECTS,
                    error_types=ERROR_TYPES,
                    chapters=CHAPTERS,
                    form_data=form_data,
                    errors=errors,
                )

        # GET: prefill
        form_data = {
            "test_name": mistake["test_name"],
            "test_date": mistake["test_date"],
            "subject": mistake["subject"],
            "chapter": mistake["chapter"],
            "error_type": mistake["error_type"],
            "question_ref": mistake["question_ref"] or "",
            "note": mistake["note"] or "",
        }
        return render_template(
            "edit.html",
            mistake=mistake,
            subjects=SUBJECTS,
            error_types=ERROR_TYPES,
            chapters=CHAPTERS,
            form_data=form_data,
            errors={},
        )

    @app.route("/mistakes/<int:mid>/delete", methods=["POST"])
    def delete_mistake_route(mid):
        """Delete a mistake."""
        db = get_db()
        # CSRF already checked in before_request
        queries.delete_mistake(db, mid)
        # Redirect back to list preserving filters
        # Preserve query string from referrer or request
        return redirect(url_for("list_mistakes"))

    @app.route("/export")
    def export_csv():
        """Export currently filtered rows as CSV."""
        db = get_db()
        subject = request.args.get("subject", "").strip() or None
        chapter = request.args.get("chapter", "").strip() or None
        error_type = request.args.get("error_type", "").strip() or None
        test_name = request.args.get("test_name", "").strip() or None
        rows = queries.get_all_for_export(db, subject=subject, chapter=chapter, error_type=error_type, test_name=test_name)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "test_name", "test_date", "subject", "chapter", "error_type", "question_ref", "note", "created_at"])
        for r in rows:
            writer.writerow([r["id"], r["test_name"], r["test_date"], r["subject"], r["chapter"], r["error_type"], r["question_ref"] or "", r["note"] or "", r["created_at"]])
        csv_data = output.getvalue()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=mistakes.csv"},
        )

    @app.route("/dashboard")
    def dashboard():
        """Dashboard with summary and charts."""
        db = get_db()
        range_param = request.args.get("range", "30")
        # Map to days: 14,30,90,all
        # Default 30
        if range_param not in ["14", "30", "90", "all"]:
            range_param = "30"

        # Compute date range
        today = datetime.date.today()
        if range_param == "all":
            start_date = None
            end_date = None
        else:
            days = int(range_param)
            start_date = (today - datetime.timedelta(days=days-1)).isoformat()
            end_date = today.isoformat()

        total = queries.get_total_in_range(db, start_date, end_date)
        most_subject = queries.get_most_error_prone_subject(db, start_date, end_date)
        most_error = queries.get_most_common_error_type(db, start_date, end_date)

        by_subject = queries.get_stats_by_subject(db, start_date, end_date)
        by_error = queries.get_stats_by_error_type(db, start_date, end_date)
        top_chapters = queries.get_top_chapters(db, start_date, end_date, limit=5)
        per_test = queries.get_mistakes_per_test(db, start_date, end_date)

        return render_template(
            "dashboard.html",
            range_param=range_param,
            total=total,
            most_subject=most_subject,
            most_error=most_error,
            by_subject=by_subject,
            by_error=by_error,
            top_chapters=top_chapters,
            per_test=per_test,
        )

    @app.route("/api/dashboard-data")
    def api_dashboard_data():
        """JSON data for dashboard charts (alternative to embedding)."""
        db = get_db()
        range_param = request.args.get("range", "30")
        if range_param not in ["14", "30", "90", "all"]:
            range_param = "30"
        today = datetime.date.today()
        if range_param == "all":
            start_date = None
            end_date = None
        else:
            days = int(range_param)
            start_date = (today - datetime.timedelta(days=days-1)).isoformat()
            end_date = today.isoformat()

        by_subject = queries.get_stats_by_subject(db, start_date, end_date)
        by_error = queries.get_stats_by_error_type(db, start_date, end_date)
        top_chapters = queries.get_top_chapters(db, start_date, end_date, limit=5)
        per_test = queries.get_mistakes_per_test(db, start_date, end_date)
        return jsonify({
            "by_subject": by_subject,
            "by_error": by_error,
            "top_chapters": top_chapters,
            "per_test": per_test,
        })

    @app.route("/revision")
    def revision():
        """Revision list page."""
        db = get_db()
        window = request.args.get("window", "28")
        if window not in ["14", "28", "60"]:
            window = "28"
        days = int(window)
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=days-1)).isoformat()
        end_date = today.isoformat()

        ranking = queries.get_revision_ranking(db, start_date=start_date, end_date=end_date, limit=10)
        # For each ranking, fetch notes
        # We will provide notes via separate expansion; but pre-fetch for template
        enriched = []
        for item in ranking:
            notes_rows = queries.get_notes_for_chapter(db, item["chapter"], item["subject"], start_date, end_date)
            notes = []
            for nr in notes_rows:
                if nr["note"]:
                    notes.append({
                        "note": nr["note"],
                        "question_ref": nr["question_ref"],
                        "test_name": nr["test_name"],
                        "test_date": nr["test_date"],
                        "error_type": nr["error_type"],
                    })
            enriched.append({**item, "notes": notes})

        return render_template(
            "revision.html",
            window=window,
            ranking=enriched,
            start_date=start_date,
            end_date=end_date,
        )

    return app
