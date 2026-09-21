from datetime import datetime

from flask import Blueprint, jsonify, session

from backend.db import get_db_connection

student_dashboard_bp = Blueprint('student_dashboard', __name__, url_prefix='/api/student/dashboard')

SESSION_KEY = 'student_id'  # must match the key used in app.py login()

ATTENDANCE_WINDOW_DAYS = 30
DAY_ABBR = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}


def _format_time(value):
    return value.strftime('%H:%M') if hasattr(value, 'strftime') else str(value)


@student_dashboard_bp.route('/summary', methods=['GET'])
def student_dashboard_summary():
    """GET /api/student/dashboard/summary -> aggregate stats for the logged-in student."""
    student_id = session.get(SESSION_KEY)
    if not student_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS assignment_submissions (
                    id SERIAL PRIMARY KEY,
                    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
                    student_id INTEGER NOT NULL REFERENCES student_signup(id) ON DELETE CASCADE,
                    submission_text TEXT,
                    submission_url TEXT,
                    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (assignment_id, student_id)
                )
                """
            )
            conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.class_name, c.subject, m.fullname
                   FROM student_classes sc
                   JOIN classes c ON c.id = sc.class_id
                   JOIN mentor_signup m ON m.id = c.created_by
                   WHERE sc.student_id = %s
                   ORDER BY c.class_name""",
                (student_id,)
            )
            teachers = [
                {"class_id": r[0], "class_name": r[1], "subject": r[2], "mentor_name": r[3]}
                for r in cur.fetchall()
            ]

            cur.execute(
                """SELECT
                       COUNT(*) FILTER (WHERE status = 'present') AS present_count,
                       COUNT(*) AS total_count
                   FROM attendance
                   WHERE student_id = %s
                     AND date >= CURRENT_DATE - (%s * INTERVAL '1 day')""",
                (student_id, ATTENDANCE_WINDOW_DAYS)
            )
            present_count, total_count = cur.fetchone()
            attendance = (
                {"percent": round(present_count / total_count * 100), "present": present_count, "total": total_count}
                if total_count else None
            )

            cur.execute(
                """SELECT AVG(m.score / e.max_marks) * 100
                   FROM marks m
                   JOIN exams e ON e.id = m.exam_id
                   WHERE m.student_id = %s""",
                (student_id,)
            )
            avg_marks = cur.fetchone()[0]
            performance = {"percent": round(float(avg_marks))} if avg_marks is not None else None

            cur.execute(
                """SELECT
                       COUNT(*) FILTER (WHERE sub.id IS NOT NULL) AS done_count,
                       COUNT(*) AS total_count
                   FROM assignments a
                   JOIN student_classes sc ON sc.class_id = a.class_id AND sc.student_id = %s
                   LEFT JOIN assignment_submissions sub
                     ON sub.assignment_id = a.id AND sub.student_id = %s""",
                (student_id, student_id)
            )
            done_count, hw_total = cur.fetchone()
            homework = (
                {"percent": round(done_count / hw_total * 100), "done": done_count, "total": hw_total}
                if hw_total else None
            )

            today_abbr = DAY_ABBR[datetime.now().weekday()]
            cur.execute(
                """SELECT t.subject, t.start_time, t.end_time, t.room, c.class_name
                   FROM class_timetable t
                   JOIN classes c ON c.id = t.class_id
                   JOIN student_classes sc ON sc.class_id = c.id
                   WHERE sc.student_id = %s AND t.day_of_week = %s
                   ORDER BY t.start_time""",
                (student_id, today_abbr)
            )
            today_schedule = [
                {
                    "subject": r[0], "start_time": _format_time(r[1]),
                    "end_time": _format_time(r[2]), "room": r[3], "class_name": r[4],
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                """SELECT n.title, n.content, n.created_at, c.class_name, m.fullname
                   FROM mentor_notes n
                   JOIN classes c ON c.id = n.class_id
                   JOIN mentor_signup m ON m.id = n.mentor_id
                   JOIN student_classes sc ON sc.class_id = c.id
                   WHERE sc.student_id = %s
                   ORDER BY n.created_at DESC
                   LIMIT 5""",
                (student_id,)
            )
            recent_notes = [
                {
                    "title": r[0], "content": r[1], "created_at": r[2].isoformat(),
                    "class_name": r[3], "mentor_name": r[4],
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({
        "teachers": teachers,
        "attendance": attendance,
        "performance": performance,
        "homework": homework,
        "today_schedule": today_schedule,
        "recent_notes": recent_notes,
        "recent_attendance": recent_attendance,
    }), 200