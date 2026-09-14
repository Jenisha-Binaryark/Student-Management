from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / classes.py
VALID_STATUSES = {'present', 'absent'}


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


@attendance_bp.route('', methods=['GET'])
def get_attendance():
    """GET /api/attendance?class_id=..&date=YYYY-MM-DD -> roster merged with that date's status."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    class_id = request.args.get('class_id')
    date = request.args.get('date')

    if not class_id or not date:
        return jsonify({"error": "class_id and date are required"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """SELECT s.id, s.fullname, s.email, a.status
               FROM student_classes sc
               JOIN student_signup s ON s.id = sc.student_id
               LEFT JOIN attendance a
                 ON a.student_id = s.id AND a.class_id = sc.class_id AND a.date = %s
               WHERE sc.class_id = %s
               ORDER BY s.fullname""",
            (date, class_id)
        )
        rows = cur.fetchall()
    conn.close()

    records = [
        {"student_id": r[0], "fullname": r[1], "email": r[2], "status": r[3]}
        for r in rows
    ]
    return jsonify({"date": date, "records": records}), 200


@attendance_bp.route('', methods=['POST'])
def save_attendance():
    """POST /api/attendance {class_id, date, records:[{student_id, status}]} -> upsert marks."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')
    date = (data.get('date') or '').strip()
    records = data.get('records') or []

    if not class_id or not date:
        return jsonify({"error": "class_id and date are required"}), 400
    if not isinstance(records, list) or not records:
        return jsonify({"error": "At least one attendance record is required"}), 400

    for r in records:
        if r.get('status') not in VALID_STATUSES:
            return jsonify({"error": "Each record needs status 'present' or 'absent'"}), 400
        if not r.get('student_id'):
            return jsonify({"error": "Each record needs a student_id"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        for r in records:
            cur.execute(
                """INSERT INTO attendance (class_id, student_id, mentor_id, date, status)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (class_id, student_id, date)
                   DO UPDATE SET status = EXCLUDED.status, mentor_id = EXCLUDED.mentor_id""",
                (class_id, r['student_id'], mentor_id, date, r['status'])
            )
        conn.commit()
    conn.close()

    return jsonify({"message": "Attendance saved"}), 200