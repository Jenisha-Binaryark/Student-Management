from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection

student_content_bp = Blueprint('student_content', __name__, url_prefix='/api/student')

@student_content_bp.route('/content', methods=['GET'])
def student_content():
    student_id = session.get('student_id')
    if session.get('role') != 'student' or not student_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.class_name, c.subject, m.fullname
                FROM student_classes sc
                JOIN classes c ON c.id = sc.class_id
                JOIN mentor_signup m ON m.id = c.created_by
                WHERE sc.student_id = %s
                ORDER BY c.class_name
                """,
                (student_id,)
            )
            classes = [
                {'id': r[0], 'class_name': r[1], 'subject': r[2], 'mentor_name': r[3]}
                for r in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT a.id, a.class_id, c.class_name, a.title, a.description,
                       a.due_date, a.created_at,
                       s.id, s.submission_text, s.submission_url, s.submitted_at
                FROM assignments a
                JOIN classes c ON c.id = a.class_id
                JOIN student_classes sc ON sc.class_id = a.class_id AND sc.student_id = %s
                LEFT JOIN assignment_submissions s
                  ON s.assignment_id = a.id AND s.student_id = %s
                ORDER BY a.due_date ASC, a.created_at DESC
                """,
                (student_id, student_id)
            )
            assignments = [
                {
                    'id': r[0],
                    'class_id': r[1],
                    'class_name': r[2],
                    'title': r[3],
                    'description': r[4],
                    'due_date': r[5].isoformat(),
                    'created_at': r[6].isoformat(),
                    'submission': {
                        'id': r[7],
                        'text': r[8],
                        'url': r[9],
                        'submitted_at': r[10].isoformat()
                    } if r[7] else None
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT n.id, n.class_id, c.class_name, m.fullname,
                       n.title, n.content, n.created_at
                FROM mentor_notes n
                JOIN classes c ON c.id = n.class_id
                JOIN mentor_signup m ON m.id = n.mentor_id
                JOIN student_classes sc ON sc.class_id = n.class_id
                WHERE sc.student_id = %s
                ORDER BY n.created_at DESC
                """,
                (student_id,)
            )
            notes = [
                {
                    'id': r[0], 'class_id': r[1], 'class_name': r[2],
                    'mentor_name': r[3], 'title': r[4], 'content': r[5],
                    'created_at': r[6].isoformat()
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT t.id, t.class_id, c.class_name, t.day_of_week,
                       t.subject, t.start_time, t.end_time, t.room, t.timetable_type, t.exam_date
                FROM class_timetable t
                JOIN classes c ON c.id = t.class_id
                JOIN student_classes sc ON sc.class_id = t.class_id
                WHERE sc.student_id = %s
                ORDER BY t.day_of_week, t.start_time
                """,
                (student_id,)
            )
            timetable = [
                {
                    'id': r[0], 'class_id': r[1], 'class_name': r[2],
                    'day_of_week': r[3], 'subject': r[4],
                    'start_time': r[5].strftime('%H:%M'),
                    'end_time': r[6].strftime('%H:%M'),
                    'room': r[7], 'timetable_type': r[8], 'exam_date': r[9].isoformat() if r[9] else None
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT e.id, e.class_id, c.class_name, e.title, e.max_marks,
                       e.exam_date, m.score
                FROM exams e
                JOIN classes c ON c.id = e.class_id
                JOIN student_classes sc ON sc.class_id = e.class_id
                LEFT JOIN marks m ON m.exam_id = e.id AND m.student_id = %s
                WHERE sc.student_id = %s
                ORDER BY e.exam_date DESC
                """,
                (student_id, student_id)
            )
            exams = [
                {
                    'id': r[0], 'class_id': r[1], 'class_name': r[2],
                    'title': r[3], 'max_marks': float(r[4]),
                    'exam_date': r[5].isoformat(),
                    'score': float(r[6]) if r[6] is not None else None
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT a.class_id, c.class_name, a.date, a.status
                FROM attendance a
                JOIN classes c ON c.id = a.class_id
                JOIN student_classes sc ON sc.class_id = a.class_id
                WHERE a.student_id = %s
                ORDER BY a.date DESC
                """,
                (student_id,)
            )
            attendance = [
                {'class_id': r[0], 'class_name': r[1], 'date': r[2].isoformat(), 'status': r[3]}
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({
        'classes': classes,
        'assignments': assignments,
        'notes': notes,
        'timetable': timetable,
        'exams': exams,
        'attendance': attendance
    }), 200

@student_content_bp.route('/assignments/<int:assignment_id>/submission', methods=['POST'])
def submit_assignment(assignment_id):
    student_id = session.get('student_id')
    if session.get('role') != 'student' or not student_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    submission_text = (data.get('text') or '').strip()
    submission_url = (data.get('url') or '').strip()

    if not submission_text and not submission_url:
        return jsonify({'error': 'Submission text or URL is required'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id
                FROM assignments a
                JOIN student_classes sc ON sc.class_id = a.class_id
                WHERE a.id = %s AND sc.student_id = %s
                """,
                (assignment_id, student_id)
            )
            if not cur.fetchone():
                return jsonify({'error': 'Assignment not found'}), 404

            cur.execute(
                """
                INSERT INTO assignment_submissions
                    (assignment_id, student_id, submission_text, submission_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (assignment_id, student_id)
                DO UPDATE SET
                    submission_text = EXCLUDED.submission_text,
                    submission_url = EXCLUDED.submission_url,
                    updated_at = CURRENT_TIMESTAMP,
                    submitted_at = CURRENT_TIMESTAMP
                RETURNING id, submitted_at
                """,
                (assignment_id, student_id, submission_text or None, submission_url or None)
            )
            submission_id, submitted_at = cur.fetchone()
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({
        'message': 'Assignment submitted',
        'submission': {
            'id': submission_id,
            'text': submission_text or None,
            'url': submission_url or None,
            'submitted_at': submitted_at.isoformat()
        }
    }), 200
