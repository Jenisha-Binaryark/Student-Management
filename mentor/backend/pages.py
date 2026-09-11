from flask import Blueprint, render_template, redirect, url_for, session

mentor_pages_bp = Blueprint(
    "mentor_pages",
    __name__,
    template_folder="../frontend/pages",
    static_folder="../frontend",
    static_url_path="/mentor/static",
)

SESSION_KEY = "mentor_id"


def _require_mentor():
    return SESSION_KEY in session


@mentor_pages_bp.route("/mentor/onboarding.html")
def mentor_onboarding_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("onboarding.html")


@mentor_pages_bp.route("/mentor/dashboard.html")
def mentor_dashboard_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("mentor_dashboard.html")


@mentor_pages_bp.route("/mentor/sidebar.html")
def mentor_sidebar():
    if not _require_mentor():
        return {"status": "not_logged_in"}, 401
    return render_template("mentor_sidebar.html")


@mentor_pages_bp.route("/mentor/attendance.html")
def mentor_attendance_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("attendance.html")


@mentor_pages_bp.route("/mentor/timetable.html")
def mentor_timetable_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("timetable.html")


@mentor_pages_bp.route("/mentor/assignments.html")
def mentor_assignments_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("assignments.html")


@mentor_pages_bp.route("/mentor/marks.html")
def mentor_marks_page():
    if not _require_mentor():
        return redirect(url_for("login_page"))
    return render_template("marks.html")