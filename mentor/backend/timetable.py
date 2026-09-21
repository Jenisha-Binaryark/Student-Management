from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection
from mentor.backend.decorators import require_onboarding_complete

timetable_bp = Blueprint('timetable', __name__, url_prefix='/api/timetable')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / classes.py / notes.py

DAY_ORDER = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
TIMETABLE_TYPES = {'regular', 'exam'}
TIMETABLE_TYPES = {'regular', 'exam'}


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


def _format_time(value):
    return value.strftime('%H:%M') if hasattr(value, 'strftime') else str(value)


@timetable_bp.route('', methods=['POST'])
@require_onboarding_complete
def create_slot():
    """POST /api/timetable -> add a weekly slot to one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')
    day_of_week = (data.get('day_of_week') or '').strip()
    subject = (data.get('subject') or '').strip()
    start_time = (data.get('start_time') or '').strip()
    end_time = (data.get('end_time') or '').strip()
    room = (data.get('room') or '').strip()
    timetable_type = (data.get('timetable_type') or 'regular').strip().lower()
    timetable_type = (data.get('timetable_type') or 'regular').strip().lower()

    if not class_id:
        return jsonify({"error": "class_id is required"}), 400
    if timetable_type not in TIMETABLE_TYPES:
        return jsonify({"error": "timetable_type must be regular or exam"}), 400
    if timetable_type not in TIMETABLE_TYPES:
        return jsonify({"error": "timetable_type must be regular or exam"}), 400
    if day_of_week not in DAY_ORDER:
        return jsonify({"error": "day_of_week must be one of Mon, Tue, Wed, Thu, Fri, Sat, Sun"}), 400
    if not subject or not start_time or not end_time:
        return jsonify({"error": "Subject, start time, and end time are required"}), 400
    if end_time <= start_time:
        return jsonify({"error": "End time must be after start time"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO class_timetable
               (class_id, mentor_id, day_of_week, subject, start_time, end_time, room, timetable_type)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (class_id, mentor_id, day_of_week, subject, start_time, end_time, room or None, timetable_type)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    conn.close()

    return jsonify({
        "message": "Slot added",
        "slot": {
            "id": new_id,
            "class_id": class_id,
            "day_of_week": day_of_week,
            "subject": subject,
            "start_time": start_time,
            "end_time": end_time,
            "room": room or None,
        }
    }), 201


@timetable_bp.route('', methods=['GET'])
@require_onboarding_complete
def list_slots():
    """GET /api/timetable?class_id=.. -> the weekly slots for one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({"error": "class_id is required"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, day_of_week, subject, start_time, end_time, room, timetable_type, timetable_type
               FROM class_timetable
               WHERE class_id = %s AND timetable_type = %s""",
            (class_id, request.args.get('timetable_type', 'regular'))
        )
        rows = cur.fetchall()
    conn.close()

    slots = [
        {
            "id": r[0],
            "day_of_week": r[1],
            "subject": r[2],
            "start_time": _format_time(r[3]),
            "end_time": _format_time(r[4]),
            "room": r[5],
        }
        for r in rows
    ]
    slots.sort(key=lambda s: (DAY_ORDER.get(s['day_of_week'], 7), s['start_time']))

    return jsonify({"slots": slots}), 200


@timetable_bp.route('/<int:slot_id>', methods=['DELETE'])
@require_onboarding_complete
def delete_slot(slot_id):
    """DELETE /api/timetable/<id> -> remove a slot the mentor owns."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM class_timetable WHERE id = %s AND mentor_id = %s RETURNING id",
            (slot_id, mentor_id)
        )
        deleted = cur.fetchone()
        conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"error": "Slot not found"}), 404

    return jsonify({"message": "Slot deleted"}), 200