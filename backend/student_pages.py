from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from backend.db import get_db_connection

student_pages_bp = Blueprint("student_pages", __name__)


def _student_page(template):
    if session.get("role") != "student" or not session.get("student_id"):
        return redirect(url_for("login_page", role="student"))
    return render_template(template)


@student_pages_bp.get("/grades.html")
def grades_page():
    return _student_page("grades.html")


@student_pages_bp.get("/schedule.html")
def schedule_page():
    return _student_page("schedule.html")


@student_pages_bp.get("/messages.html")
def messages_page():
    return _student_page("messages.html")


@student_pages_bp.get("/settings.html")
def settings_page():
    return _student_page("settings.html")


@student_pages_bp.route("/api/student/profile", methods=["GET", "PATCH"])
def student_profile():
    student_id = session.get("student_id")
    if session.get("role") != "student" or not student_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if request.method == "PATCH":
                data = request.get_json(silent=True) or {}
                fullname = str(data.get("fullname") or "").strip()
                phone = str(data.get("phone") or "").strip()
                if not fullname or not phone:
                    return jsonify({"error": "Full name and phone are required"}), 400
                cur.execute(
                    """
                    UPDATE student_signup
                    SET fullname = %s, phone = %s
                    WHERE id = %s
                    RETURNING id, fullname, email, phone
                    """,
                    (fullname, phone, student_id),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Student not found"}), 404
                conn.commit()
                session["fullname"] = row[1]
            else:
                cur.execute(
                    """
                    SELECT id, fullname, email, phone
                    FROM student_signup
                    WHERE id = %s
                    """,
                    (student_id,),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Student not found"}), 404
    finally:
        conn.close()

    return jsonify({
        "id": row[0],
        "fullname": row[1],
        "email": row[2],
        "phone": row[3],
    })
