from flask import Flask, send_from_directory, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

app = Flask(
    __name__,
    static_folder="../frontend"
)

def get_db_connection():
    return psycopg2.connect(
        dbname = "signup_user",
        user = "postgres",
        password = "root",
        host = "localhost",
        port = "5432"
    )

@app.route("/")
def home():
    return send_from_directory("../frontend", "signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    role = data.get("role")
    referral = data.get("referral")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM signup_user WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return jsonify({"status": "exists"})

        hashed_password = generate_password_hash(password)

        cur.execute(
            """INSERT INTO signup_user (fullname, email, phone, password, role, referral)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (fullname, email, phone, hashed_password, role, referral)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "created"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": "Server error"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT password FROM signup_user WHERE email = %s OR phone = %s",
            (username, username)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return jsonify({"status": "not_found"})

        stored_hash = user[0]

        if not check_password_hash(stored_hash, password):
            return jsonify({"status": "wrong_password"})

        return jsonify({"status": "success"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)