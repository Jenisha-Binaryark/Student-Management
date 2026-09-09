from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection  # <-- adjust import path if yours differs

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

SESSION_KEY = 'mentor_id'


def get_onboarding_status(mentor_id, conn):

    with conn.cursor() as cur:
        cur.execute(
            "SELECT department, designation FROM mentor_signup WHERE id = %s",
            (mentor_id,)
        )
        row = cur.fetchone()

    department, designation = (row[0], row[1]) if row else (None, None)
    step2_done = bool(department and designation)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM classes WHERE created_by = %s",
            (mentor_id,)
        )
        class_count = cur.fetchone()[0]
    step3_done = class_count > 0

    return {
        "steps": [
            {"label": "Account", "done": True},  # signup already happened to be logged in
            {"label": "Profile details", "done": step2_done},
            {"label": "Create class", "done": step3_done},
        ],
        "all_complete": step2_done and step3_done
    }


@profile_bp.route('/status', methods=['GET'])
def profile_status():
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    status = get_onboarding_status(mentor_id, conn)
    return jsonify(status), 200


@profile_bp.route('/complete', methods=['POST'])
def complete_profile():
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    department = (data.get('department') or '').strip()
    designation = (data.get('designation') or '').strip()

    if not department or not designation:
        return jsonify({"error": "Department and designation are required"}), 400

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE mentor_signup SET department = %s, designation = %s WHERE id = %s",
            (department, designation, mentor_id)
        )
        conn.commit()

    return jsonify({"message": "Profile updated"}), 200