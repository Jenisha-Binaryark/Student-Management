from flask import Blueprint, render_template, redirect, url_for, session
from backend.db import get_db_connection
from mentor.backend.profile import get_onboarding_status

mentor_pages_bp = Blueprint(
    "mentor_pages",
    __name__,
    template_folder="../frontend/pages",
    static_folder="../frontend",
    static_url_path="/mentor/static",
)

SESSION_KEY = "mentor_id"


def _require_mentor():
    return session.get("role") == "mentor" and SESSION_KEY in session


def _require_onboarding_page():
    if not _require_mentor():
        return redirect(url_for("login_page", role="mentor"))

    conn = get_db_connection()
    try:
        status = get_onboarding_status(session[SESSION_KEY], conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not status.get("all_complete"):
        return redirect(url_for("mentor_pages.mentor_onboarding_page"))

    return None


@mentor_pages_bp.route("/mentor/onboarding.html")
def mentor_onboarding_page():
    if not _require_mentor():
        return redirect(url_for("login_page", role="mentor"))
    return render_template("onboarding.html")


@mentor_pages_bp.route("/mentor/dashboard.html")
def mentor_dashboard_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("mentor_dashboard.html")


@mentor_pages_bp.route("/mentor/sidebar.html")
def mentor_sidebar():
    if not _require_mentor():
        return {"status": "not_logged_in"}, 401
    return render_template("mentor_sidebar.html")


@mentor_pages_bp.route("/mentor/attendance.html")
def mentor_attendance_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("attendance.html")


@mentor_pages_bp.route("/mentor/timetable.html")
def mentor_timetable_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("timetable.html")


@mentor_pages_bp.route("/mentor/assignments.html")
def mentor_assignments_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("assignments.html")


@mentor_pages_bp.route("/mentor/marks.html")
def mentor_marks_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("marks.html")


@mentor_pages_bp.route("/mentor/notes.html")
def mentor_notes_page():
    blocked = _require_onboarding_page()
    if blocked:
        return blocked
    return render_template("notes.html")
