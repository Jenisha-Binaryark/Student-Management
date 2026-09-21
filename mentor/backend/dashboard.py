from datetime import datetime

from flask import Blueprint, jsonify, request, session

from backend.db import get_db_connection
from mentor.backend.decorators import require_onboarding_complete

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

SESSION_KEY = 'mentor_id'

ATTENDANCE_WINDOW_DAYS = 30
DAY_ABBR = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}


def _format_time(value):
    return value.strftime('%H:%M') if hasattr(value, 'strftime') else str(value)


@dashboard_bp.route('/summary', methods=['GET'])
@require_onboarding_complete
def dashboard_summary():
    """GET /api/dashboard/summary -> aggregate stats across all of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    class_id = request.args.get("class_id", type=int)
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE class_timetable ADD COLUMN IF NOT EXISTS timetable_type VARCHAR(20) NOT NULL DEFAULT 'regular'")
            cur.execute("ALTER TABLE class_timetable ADD COLUMN IF NOT EXISTS exam_date DATE")
            conn.commit()

            cur.execute(
                """SELECT c.id, c.class_name, c.course, c.subject,
                          COUNT(sc.student_id) AS student_count
                   FROM classes c
                   LEFT JOIN student_classes sc ON sc.class_id = c.id
                   WHERE c.created_by = %s
                   GROUP BY c.id, c.class_name, c.course, c.subject
                   ORDER BY c.created_at""",
                (mentor_id,)
            )
            classes = [
                {
                    "id": r[0], "class_name": r[1], "course": r[2],
                    "subject": r[3], "student_count": r[4],
                }
                for r in cur.fetchall()
            ]

            class_filter = " AND c.id = %s" if class_id is not None else ""

            if class_id is not None:
                cur.execute(
                    "SELECT id FROM classes WHERE id = %s AND created_by = %s",
                    (class_id, mentor_id)
                )
                if not cur.fetchone():
                    return jsonify({"error": "Class not found"}), 404

            cur.execute(
                f"""SELECT COUNT(DISTINCT sc.student_id)
                   FROM student_classes sc
                   JOIN classes c ON c.id = sc.class_id
                   WHERE c.created_by = %s
                     {class_filter}""",
                (mentor_id, class_id) if class_id is not None else (mentor_id,)
            )
            total_students = cur.fetchone()[0]

            cur.execute(
                f"""SELECT
                       COUNT(*) FILTER (WHERE a.status = 'present') AS present_count,
                       COUNT(*) AS total_count
                   FROM attendance a
                   JOIN classes c ON c.id = a.class_id
                   WHERE c.created_by = %s
                     AND a.date >= CURRENT_DATE - (%s * INTERVAL '1 day')
                     {class_filter}""",
                (mentor_id, ATTENDANCE_WINDOW_DAYS, class_id) if class_id is not None
                else (mentor_id, ATTENDANCE_WINDOW_DAYS)
            )
            present_count, total_count = cur.fetchone()
            attendance = (
                {"percent": round(present_count / total_count * 100), "present": present_count, "total": total_count}
                if total_count else None
            )

            cur.execute(
                f"""SELECT AVG(m.score / e.max_marks) * 100
                   FROM marks m
                   JOIN exams e ON e.id = m.exam_id
                   JOIN classes c ON c.id = e.class_id
                   WHERE c.created_by = %s
                     {class_filter}""",
                (mentor_id, class_id) if class_id is not None else (mentor_id,)
            )
            avg_marks = cur.fetchone()[0]
            marks = {"percent": round(float(avg_marks))} if avg_marks is not None else None

            cur.execute(
                f"""SELECT
                       COUNT(*) FILTER (WHERE a.due_date >= CURRENT_DATE) AS upcoming,
                       COUNT(*) FILTER (WHERE a.due_date < CURRENT_DATE) AS overdue
                   FROM assignments a
                   JOIN classes c ON c.id = a.class_id
                   WHERE c.created_by = %s
                     {class_filter}""",
                (mentor_id, class_id) if class_id is not None else (mentor_id,)
            )
            upcoming, overdue = cur.fetchone()
            assignments = {"upcoming": upcoming, "overdue": overdue}

            today_abbr = DAY_ABBR[datetime.now().weekday()]
            cur.execute(
                f"""SELECT t.subject, t.start_time, t.end_time, t.room, c.class_name
                   FROM class_timetable t
                   JOIN classes c ON c.id = t.class_id
                   WHERE c.created_by = %s AND t.day_of_week = %s
                     {class_filter}
                   ORDER BY t.start_time""",
                (mentor_id, today_abbr, class_id) if class_id is not None
                else (mentor_id, today_abbr)
            )
            today_schedule = [
                {
                    "subject": r[0], "start_time": _format_time(r[1]),
                    "end_time": _format_time(r[2]), "room": r[3], "class_name": r[4],
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                f"""SELECT n.title, n.content, n.created_at, c.class_name
                   FROM mentor_notes n
                   JOIN classes c ON c.id = n.class_id
                   WHERE n.mentor_id = %s
                     {class_filter}
                   ORDER BY n.created_at DESC
                   LIMIT 5""",
                (mentor_id, class_id) if class_id is not None else (mentor_id,)
            )
            recent_notes = [
                {
                    "title": r[0], "content": r[1],
                    "created_at": r[2].isoformat(), "class_name": r[3],
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({
        "classes": classes,
        "total_students": total_students,
        "attendance": attendance,
        "marks": marks,
        "assignments": assignments,
        "today_schedule": today_schedule,
        "recent_notes": recent_notes,
        "selected_class_id": class_id,
    }), 200