from flask import Flask, send_from_directory, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import get_db_connection

app = Flask(
    __name__,
    static_folder="../frontend",
    template_folder="../frontend"
)

app.secret_key = "zeebra&appleAreInLove"


@app.route("/")
def home():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    fullname = data.get("fullname")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    role = data.get("role")
    referral = data.get("referral")
    mentor_id = data.get("mentorId")

    if role == "mentor" and not mentor_id:
        return jsonify({
            "status": "error",
            "message": "Mentor ID is required."
        }), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if role == "student":
            cur.execute(
                "SELECT id FROM student_signup WHERE email = %s OR phone = %s",
                (email, phone)
            )

            existing_user = cur.fetchone()

            if existing_user:
                cur.close()
                conn.close()
                return jsonify({"status": "exists"})

            hashed_password = generate_password_hash(password)

            cur.execute(
                """INSERT INTO student_signup
                   (fullname, email, phone, password, referral)
                   VALUES (%s, %s, %s, %s, %s)""",
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
                """SELECT id FROM mentor_signup
                   WHERE email = %s OR phone = %s OR mentor_id = %s""",
                (email, phone, mentor_id)
            )

            existing_user = cur.fetchone()

            if existing_user:
                cur.close()
                conn.close()
                return jsonify({"status": "exists"})

            hashed_password = generate_password_hash(password)

            cur.execute(
                """INSERT INTO mentor_signup
                   (fullname, email, phone, password, mentor_id, referral)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
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
            cur.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "Invalid role."
            }), 400

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"status": "created"})

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500


@app.route("/login.html")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if role == "student":
            cur.execute(
                """SELECT fullname, password
                   FROM student_signup
                   WHERE email = %s OR phone = %s""",
                (username, username)
            )

            user = cur.fetchone()

            if not user:
                cur.close()
                conn.close()
                return jsonify({"status": "not_found"})

            fullname, stored_hash = user

            if not check_password_hash(stored_hash, password):
                cur.close()
                conn.close()
                return jsonify({"status": "wrong_password"})

            session["fullname"] = fullname
            session["role"] = "student"

            cur.close()
            conn.close()

            return jsonify({
                "status": "success",
                "role": "student"
            })

        elif role == "mentor":
            cur.execute(
                """SELECT id, fullname, password, mentor_id
                   FROM mentor_signup
                   WHERE email = %s OR phone = %s""",
                (username, username)
            )

            user = cur.fetchone()

            if not user:
                cur.close()
                conn.close()
                return jsonify({"status": "not_found"})

            pk_id, fullname, stored_hash, mentor_code = user

            if not check_password_hash(stored_hash, password):
                cur.close()
                conn.close()
                return jsonify({"status": "wrong_password"})

            session["fullname"] = fullname
            session["role"] = "mentor"
            session["mentor_id"] = pk_id          # integer PK, used by profile/classes routes
            session["mentor_code"] = mentor_code  # the formality mentor ID string

            cur.close()
            conn.close()

            return jsonify({
                "status": "success",
                "role": "mentor"
            })

        else:
            cur.close()
            conn.close()

            return jsonify({
                "status": "error",
                "message": "Invalid role."
            }), 400

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500


@app.route("/api/current_user")
def current_user():
    fullname = session.get("fullname")

    if not fullname:
        return jsonify({"status": "not_logged_in"}), 401

    return jsonify({
        "status": "success",
        "fullname": fullname
    })


@app.route('/sidebar.html')
def sidebar():
    if "fullname" not in session:
        return jsonify({"status": "not_logged_in"}), 401
    return render_template('sidebar.html')


@app.route("/dashboard.html")
def dashboard_page():
    if "fullname" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html")


@app.route("/homework.html")
def homework_page():
    if "fullname" not in session:
        return redirect(url_for("login_page"))
    return render_template("homework.html")


@app.route("/api/homework")
def get_homework():
    if "fullname" not in session:
        return jsonify({"status": "not_logged_in"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, subject, due_date, status FROM homework WHERE fullname = %s",
            (session["fullname"],)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        homework_list = [
            {"id": r[0], "title": r[1], "subject": r[2], "due_date": str(r[3]), "status": r[4]}
            for r in rows
        ]
        return jsonify({"status": "success", "homework": homework_list})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": "Server error"}), 500


@app.route("/my_classes.html")
def my_classes():
    return render_template("my_classes.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"}), 200


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

from mentor.backend.profile import profile_bp
from mentor.backend.classes import classes_bp
from mentor.backend.pages import mentor_pages_bp

app.register_blueprint(profile_bp)
app.register_blueprint(classes_bp)
app.register_blueprint(mentor_pages_bp)


if __name__ == "__main__":
    app.run(debug=True)