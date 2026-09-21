from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection
from mentor.backend.decorators import require_onboarding_complete

assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')

SESSION_KEY = 'mentor_id'


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


@assignments_bp.route('', methods=['POST'])
@require_onboarding_complete
def create_assignment():
    """POST /api/assignments -> post an assignment to one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    due_date = (data.get('due_date') or '').strip()

    if not class_id:
        return jsonify({"error": "class_id is required"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not due_date:
        return jsonify({"error": "Due date is required"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO assignments (class_id, mentor_id, title, description, due_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at""",
            (class_id, mentor_id, title, description or None, due_date)
        )
        new_id, created_at = cur.fetchone()
        conn.commit()
    conn.close()

    return jsonify({
        "message": "Assignment posted",
        "assignment": {
            "id": new_id,
            "class_id": class_id,
            "title": title,
            "description": description or None,
            "due_date": due_date,
            "created_at": created_at.isoformat(),
        }
    }), 201


@assignments_bp.route('', methods=['GET'])
@require_onboarding_complete
def list_assignments():
    """GET /api/assignments?class_id=.. -> assignments posted to one of the mentor's classes."""
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
            """SELECT id, title, description, due_date, created_at
               FROM assignments
               WHERE class_id = %s
               ORDER BY due_date ASC""",
            (class_id,)
        )
        rows = cur.fetchall()
    conn.close()

    assignments = [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "due_date": r[3].isoformat(),
            "created_at": r[4].isoformat(),
        }
        for r in rows
    ]
    return jsonify({"assignments": assignments}), 200



@assignments_bp.route('/<int:assignment_id>/submissions', methods=['GET'])
@require_onboarding_complete
def list_submissions(assignment_id):
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.fullname, s.email, sub.submission_text,
                       sub.submission_url, sub.submitted_at
                FROM assignments a
                JOIN student_classes sc ON sc.class_id = a.class_id
                JOIN student_signup s ON s.id = sc.student_id
                LEFT JOIN assignment_submissions sub
                  ON sub.assignment_id = a.id AND sub.student_id = s.id
                WHERE a.id = %s AND a.mentor_id = %s
                ORDER BY s.fullname
                """,
                (assignment_id, mentor_id)
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    submissions = [
        {
            "student_id": r[0],
            "fullname": r[1],
            "email": r[2],
            "text": r[3],
            "url": r[4],
            "submitted_at": r[5].isoformat() if r[5] else None
        }
        for r in rows
        if r[3] or r[4]
    ]
    return jsonify({"submissions": submissions}), 200

@assignments_bp.route('/<int:assignment_id>', methods=['DELETE'])
@require_onboarding_complete
def delete_assignment(assignment_id):
    """DELETE /api/assignments/<id> -> remove an assignment the mentor owns."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM assignments WHERE id = %s AND mentor_id = %s RETURNING id",
            (assignment_id, mentor_id)
        )
        deleted = cur.fetchone()
        conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"error": "Assignment not found"}), 404

    return jsonify({"message": "Assignment deleted"}), 200