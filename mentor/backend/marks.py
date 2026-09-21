from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection
from mentor.backend.decorators import require_onboarding_complete

marks_bp = Blueprint('marks', __name__, url_prefix='/api')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / classes.py / attendance.py


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


def _get_owned_exam(exam_id, mentor_id, conn):
    """Return (class_id, max_marks) for an exam owned by this mentor, or None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT class_id, max_marks FROM exams WHERE id = %s AND mentor_id = %s",
            (exam_id, mentor_id)
        )
        row = cur.fetchone()
    return row


# ===== Exams =====

@marks_bp.route('/exams', methods=['POST'])
@require_onboarding_complete
def create_exam():
    """POST /api/exams -> create an exam/assessment for one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    class_id = data.get('class_id')
    title = (data.get('title') or '').strip()
    max_marks = data.get('max_marks')
    exam_date = (data.get('exam_date') or '').strip()

    if not class_id:
        return jsonify({"error": "class_id is required"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not exam_date:
        return jsonify({"error": "Exam date is required"}), 400
    try:
        max_marks = float(max_marks)
        if max_marks <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Max marks must be a positive number"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO exams (class_id, mentor_id, title, max_marks, exam_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at""",
            (class_id, mentor_id, title, max_marks, exam_date)
        )
        new_id, created_at = cur.fetchone()
        conn.commit()
    conn.close()

    return jsonify({
        "message": "Exam created",
        "exam": {
            "id": new_id,
            "class_id": class_id,
            "title": title,
            "max_marks": max_marks,
            "exam_date": exam_date,
            "created_at": created_at.isoformat(),
        }
    }), 201


@marks_bp.route('/exams', methods=['GET'])
@require_onboarding_complete
def list_exams():
    """GET /api/exams?class_id=.. -> exams belonging to one of the mentor's classes."""
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
            """SELECT id, title, max_marks, exam_date, created_at
               FROM exams
               WHERE class_id = %s
               ORDER BY exam_date DESC""",
            (class_id,)
        )
        rows = cur.fetchall()
    conn.close()

    exams = [
        {
            "id": r[0],
            "title": r[1],
            "max_marks": float(r[2]),
            "exam_date": r[3].isoformat(),
            "created_at": r[4].isoformat(),
        }
        for r in rows
    ]
    return jsonify({"exams": exams}), 200


@marks_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@require_onboarding_complete
def delete_exam(exam_id):
    """DELETE /api/exams/<id> -> remove an exam the mentor owns (cascades its marks)."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM exams WHERE id = %s AND mentor_id = %s RETURNING id",
            (exam_id, mentor_id)
        )
        deleted = cur.fetchone()
        conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"error": "Exam not found"}), 404

    return jsonify({"message": "Exam deleted"}), 200


# ===== Marks =====

@marks_bp.route('/marks', methods=['GET'])
@require_onboarding_complete
def get_marks():
    """GET /api/marks?exam_id=.. -> roster merged with each student's score for that exam."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    exam_id = request.args.get('exam_id')
    if not exam_id:
        return jsonify({"error": "exam_id is required"}), 400

    conn = get_db_connection()

    exam = _get_owned_exam(exam_id, mentor_id, conn)
    if not exam:
        conn.close()
        return jsonify({"error": "Exam not found"}), 404
    class_id, max_marks = exam

    with conn.cursor() as cur:
        cur.execute(
            """SELECT s.id, s.fullname, s.email, m.score
               FROM student_classes sc
               JOIN student_signup s ON s.id = sc.student_id
               LEFT JOIN marks m
                 ON m.student_id = s.id AND m.exam_id = %s
               WHERE sc.class_id = %s
               ORDER BY s.fullname""",
            (exam_id, class_id)
        )
        rows = cur.fetchall()
    conn.close()

    records = [
        {
            "student_id": r[0],
            "fullname": r[1],
            "email": r[2],
            "score": float(r[3]) if r[3] is not None else None,
        }
        for r in rows
    ]
    return jsonify({"max_marks": float(max_marks), "records": records}), 200


@marks_bp.route('/marks', methods=['POST'])
@require_onboarding_complete
def save_marks():
    """POST /api/marks {exam_id, records:[{student_id, score}]} -> upsert scores."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    exam_id = data.get('exam_id')
    records = data.get('records') or []

    if not exam_id:
        return jsonify({"error": "exam_id is required"}), 400
    if not isinstance(records, list) or not records:
        return jsonify({"error": "At least one mark record is required"}), 400

    conn = get_db_connection()

    exam = _get_owned_exam(exam_id, mentor_id, conn)
    if not exam:
        conn.close()
        return jsonify({"error": "Exam not found"}), 404
    _, max_marks = exam
    max_marks = float(max_marks)

    parsed = []
    for r in records:
        if not r.get('student_id'):
            conn.close()
            return jsonify({"error": "Each record needs a student_id"}), 400
        try:
            score = float(r.get('score'))
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Each record needs a numeric score"}), 400
        if score < 0 or score > max_marks:
            conn.close()
            return jsonify({"error": f"Score must be between 0 and {max_marks}"}), 400
        parsed.append((r['student_id'], score))

    with conn.cursor() as cur:
        for student_id, score in parsed:
            cur.execute(
                """INSERT INTO marks (exam_id, student_id, mentor_id, score, updated_at)
                   VALUES (%s, %s, %s, %s, NOW())
                   ON CONFLICT (exam_id, student_id)
                   DO UPDATE SET score = EXCLUDED.score, mentor_id = EXCLUDED.mentor_id, updated_at = NOW()""",
                (exam_id, student_id, mentor_id, score)
            )
        conn.commit()
    conn.close()

    return jsonify({"message": "Marks saved"}), 200