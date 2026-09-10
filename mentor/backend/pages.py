from flask import Blueprint, render_template, redirect, url_for, session

mentor_pages_bp = Blueprint(
    "mentor_pages",
    __name__,
    template_folder="../frontend/pages",
    static_folder="../frontend",
    static_url_path="/mentor/static",
)

SESSION_KEY = "mentor_id"


@mentor_pages_bp.route("/mentor/onboarding.html")
def mentor_onboarding_page():
    if SESSION_KEY not in session:
        return redirect(url_for("login_page"))
    return render_template("onboarding.html")


@mentor_pages_bp.route("/mentor/dashboard.html")
def mentor_dashboard_page():
    if SESSION_KEY not in session:
        return redirect(url_for("login_page"))
    return render_template("/mentor/dashboard.html")