from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection

classes_bp = Blueprint('classes', __name__, url_prefix='/api/classes')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / login route

REQUIRED_FIELDS = ['class_name', 'university', 'course', 'year', 'subject', 'role']


@classes_bp.route('', methods=['POST'])
def create_class():
    """POST /api/classes -> create a new class, tied to the logged-in mentor."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    missing = [f for f in REQUIRED_FIELDS if not (data.get(f) or '').strip()
               if isinstance(data.get(f), str)] + \
              [f for f in REQUIRED_FIELDS if data.get(f) is None]
    missing = list(dict.fromkeys(missing))  # dedupe, keep order

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if data['role'] not in ('mentor', 'teacher'):
        return jsonify({"error": "Role must be 'mentor' or 'teacher'"}), 400

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO classes
               (class_name, university, course, year, subject, role, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                data['class_name'].strip(),
                data['university'].strip(),
                data['course'].strip(),
                str(data['year']).strip(),
                data['subject'].strip(),
                data['role'],
                mentor_id,
            )
        )
        new_id = cur.fetchone()[0]
        conn.commit()

    return jsonify({"message": "Class created", "class_id": new_id}), 201


@classes_bp.route('', methods=['GET'])
def list_classes():
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, class_name, university, course, year, subject, role
               FROM classes WHERE created_by = %s ORDER BY created_at""",
            (mentor_id,)
        )
        rows = cur.fetchall()

    classes = [
        {
            "id": r[0], "class_name": r[1], "university": r[2],
            "course": r[3], "year": r[4], "subject": r[5], "role": r[6],
        }
        for r in rows
    ]
    return jsonify({"classes": classes}), 200