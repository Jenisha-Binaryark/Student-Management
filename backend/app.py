import os
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from backend.config import SECRET_KEY, APP_ENV, SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE, SESSION_LIFETIME
from backend.db import get_db_connection
from backend.security import auth_rate_limit

from mentor.backend.profile import profile_bp
from mentor.backend.classes import classes_bp
from mentor.backend.notes import notes_bp
from mentor.backend.timetable import timetable_bp
from mentor.backend.roster import roster_bp
from mentor.backend.attendance import attendance_bp
from mentor.backend.assignments import assignments_bp
from mentor.backend.marks import marks_bp
from mentor.backend.dashboard import dashboard_bp
from mentor.backend.pages import mentor_pages_bp
from backend.student_dashboard import student_dashboard_bp
from backend.student_content import student_content_bp


app = Flask(
    __name__,
    static_folder="../frontend",
    template_folder="../frontend"
)

app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY=SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
    PERMANENT_SESSION_LIFETIME=SESSION_LIFETIME,
)


@app.route("/")
def home():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
@auth_rate_limit
def signup():
    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request data."
        }), 400

    fullname = data.get("fullname")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    role = data.get("role")
    referral = data.get("referral")
    mentor_id = data.get("mentorId")

    if not fullname or not email or not phone or not password or not role:
        return jsonify({
            "status": "error",
            "message": "Required fields are missing."
        }), 400

    if role == "mentor" and not mentor_id:
        return jsonify({
            "status": "error",
            "message": "Mentor ID is required."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if role == "student":
            cur.execute(
                """
                SELECT id
                FROM student_signup
                WHERE email = %s OR phone = %s
                """,
                (email, phone)
            )

            existing_user = cur.fetchone()

            if existing_user:
                return jsonify({
                    "status": "exists"
                })

            hashed_password = generate_password_hash(password)

            cur.execute(
                """
                INSERT INTO student_signup
                (fullname, email, phone, password, referral)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    fullname,
                    email,
                    phone,
                    hashed_password,
                    referral
                )
            )

        elif role == "mentor":
            cur.execute(
                """
                SELECT id
                FROM mentor_signup
                WHERE email = %s
                   OR phone = %s
                   OR mentor_id = %s
                """,
                (email, phone, mentor_id)
            )

            existing_user = cur.fetchone()

            if existing_user:
                return jsonify({
                    "status": "exists"
                })

            hashed_password = generate_password_hash(password)

            cur.execute(
                """
                INSERT INTO mentor_signup
                (fullname, email, phone, password, mentor_id, referral)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    fullname,
                    email,
                    phone,
                    hashed_password,
                    mentor_id,
                    referral
                )
            )

        else:
            return jsonify({
                "status": "error",
                "message": "Invalid role."
            }), 400

        conn.commit()

        return jsonify({
            "status": "created"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("SIGNUP ERROR:", repr(e))

        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/login.html")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
@auth_rate_limit
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request data."
        }), 400

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return jsonify({
            "status": "error",
            "message": "Username, password and role are required."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if role == "student":
            cur.execute(
                """
                SELECT id, fullname, password
                FROM student_signup
                WHERE email = %s OR phone = %s
                """,
                (username, username)
            )

            user = cur.fetchone()

            if not user:
                return jsonify({
                    "status": "not_found"
                })

            pk_id, fullname, stored_hash = user

            if not check_password_hash(stored_hash, password):
                return jsonify({
                    "status": "wrong_password"
                })

            session.clear()

            session["fullname"] = fullname
            session["role"] = "student"
            session["student_id"] = pk_id

            return jsonify({
                "status": "success",
                "role": "student"
            })

        elif role == "mentor":
            cur.execute(
                """
                SELECT id, fullname, password, mentor_id
                FROM mentor_signup
                WHERE email = %s
                   OR phone = %s
                   OR mentor_id = %s
                """,
                (username, username, username)
            )

            user = cur.fetchone()

            if not user:
                return jsonify({
                    "status": "not_found"
                })

            pk_id, fullname, stored_hash, mentor_code = user

            if not check_password_hash(stored_hash, password):
                return jsonify({
                    "status": "wrong_password"
                })

            session.clear()

            session["fullname"] = fullname
            session["role"] = "mentor"
            session["mentor_id"] = pk_id
            session["mentor_code"] = mentor_code

            return jsonify({
                "status": "success",
                "role": "mentor"
            })

        else:
            return jsonify({
                "status": "error",
                "message": "Invalid role."
            }), 400

    except Exception as e:
        print("LOGIN ERROR:", repr(e))

        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/api/current_user")
def current_user():
    fullname = session.get("fullname")

    if not fullname:
        return jsonify({
            "status": "not_logged_in"
        }), 401

    return jsonify({
        "status": "success",
        "fullname": fullname
    })


@app.route("/sidebar.html")
def sidebar():
    if session.get("role") != "student" or "student_id" not in session:
        return redirect(url_for("login_page", role="student"))

    return render_template("sidebar.html")


@app.route("/dashboard.html")
def dashboard_page():
    if session.get("role") != "student" or "student_id" not in session:
        return redirect(url_for("login_page", role="student"))

    return render_template("dashboard.html")


@app.route("/homework.html")
def homework_page():
    if session.get("role") != "student" or "student_id" not in session:
        return redirect(url_for("login_page", role="student"))

    return render_template("homework.html")


@app.route("/api/homework")
def get_homework():
    if "student_id" not in session:
        return jsonify({
            "status": "not_logged_in"
        }), 401

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, title, subject, due_date, status
            FROM homework
            WHERE student_id = %s
            """,
            (session["student_id"],)
        )

        rows = cur.fetchall()

        homework_list = [
            {
                "id": row[0],
                "title": row[1],
                "subject": row[2],
                "due_date": str(row[3]),
                "status": row[4]
            }
            for row in rows
        ]

        return jsonify({
            "status": "success",
            "homework": homework_list
        })

    except Exception as e:
        print("HOMEWORK ERROR:", repr(e))

        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/my_classes.html")
def my_classes():
    if session.get("role") != "student" or "student_id" not in session:
        return redirect(url_for("login_page", role="student"))

    return render_template("my_classes.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "status": "success"
    }), 200


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.register_blueprint(profile_bp)
app.register_blueprint(classes_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(roster_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(assignments_bp)
app.register_blueprint(marks_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(mentor_pages_bp)
app.register_blueprint(student_dashboard_bp)
app.register_blueprint(student_content_bp)


if __name__ == "__main__":
    app.run(debug=APP_ENV != "production")
