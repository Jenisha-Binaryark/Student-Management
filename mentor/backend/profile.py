from flask import Blueprint, request, jsonify, session

from backend.db import get_db_connection

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

        cur.execute(
            "SELECT COUNT(*) FROM classes WHERE created_by = %s",
            (mentor_id,)
        )
        class_count = cur.fetchone()[0]

    return {
        "steps": [
            {"label": "Account", "done": True},
            {"label": "Profile details", "done": step2_done},
            {"label": "Create class", "done": class_count > 0},
        ],
        "all_complete": step2_done and class_count > 0,
    }


@profile_bp.route('/status', methods=['GET'])
def profile_status():
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        status = get_onboarding_status(mentor_id, conn)
    finally:
        conn.close()

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
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mentor_signup SET department = %s, designation = %s WHERE id = %s",
                (department, designation, mentor_id)
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({"message": "Profile updated"}), 200


@profile_bp.route('/details', methods=['GET', 'PATCH'])
def profile_details():
    mentor_id = session.get(SESSION_KEY)
    if session.get('role') != 'mentor' or not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if request.method == 'PATCH':
                data = request.get_json(silent=True) or {}
                fullname = (data.get('fullname') or '').strip()
                phone = (data.get('phone') or '').strip()
                department = (data.get('department') or '').strip()
                designation = (data.get('designation') or '').strip()
                if not all((fullname, phone, department, designation)):
                    return jsonify({"error": "All profile fields are required"}), 400
                cur.execute(
                    """
                    UPDATE mentor_signup
                    SET fullname = %s, phone = %s, department = %s, designation = %s
                    WHERE id = %s
                    RETURNING id, fullname, email, phone, department, designation, mentor_id
                    """,
                    (fullname, phone, department, designation, mentor_id),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Mentor not found"}), 404
                conn.commit()
                session['fullname'] = row[1]
            else:
                cur.execute(
                    """
                    SELECT id, fullname, email, phone, department, designation, mentor_id
                    FROM mentor_signup WHERE id = %s
                    """,
                    (mentor_id,),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Mentor not found"}), 404
    finally:
        conn.close()

    return jsonify({
        'id': row[0], 'fullname': row[1], 'email': row[2], 'phone': row[3],
        'department': row[4], 'designation': row[5], 'mentor_id': row[6]
    }), 200
