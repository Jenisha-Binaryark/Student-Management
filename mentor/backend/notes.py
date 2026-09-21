from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection
from mentor.backend.decorators import require_onboarding_complete

notes_bp = Blueprint('notes', __name__, url_prefix='/api/notes')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / classes.py


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


@notes_bp.route('', methods=['POST'])
@require_onboarding_complete
def create_note():
    """POST /api/notes -> post a note to students in one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()

    if not class_id:
        return jsonify({"error": "class_id is required"}), 400
    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO mentor_notes (class_id, mentor_id, title, content)
               VALUES (%s, %s, %s, %s) RETURNING id, created_at""",
            (class_id, mentor_id, title, content)
        )
        new_id, created_at = cur.fetchone()
        conn.commit()

    return jsonify({
        "message": "Note posted",
        "note": {
            "id": new_id,
            "class_id": class_id,
            "title": title,
            "content": content,
            "created_at": created_at.isoformat()
        }
    }), 201


@notes_bp.route('', methods=['GET'])
@require_onboarding_complete
def list_notes():
    """GET /api/notes[?class_id=..] -> notes posted by the logged-in mentor."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    class_id = request.args.get('class_id')

    conn = get_db_connection()

    query = """SELECT n.id, n.class_id, c.class_name, n.title, n.content, n.created_at
               FROM mentor_notes n
               JOIN classes c ON c.id = n.class_id
               WHERE n.mentor_id = %s"""
    params = [mentor_id]

    if class_id:
        query += " AND n.class_id = %s"
        params.append(class_id)

    query += " ORDER BY n.created_at DESC LIMIT 100"

    with conn.cursor() as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

    notes = [
        {
            "id": r[0],
            "class_id": r[1],
            "class_name": r[2],
            "title": r[3],
            "content": r[4],
            "created_at": r[5].isoformat(),
        }
        for r in rows
    ]
    return jsonify({"notes": notes}), 200