from flask import Blueprint, request, jsonify, session
from backend.db import get_db_connection

roster_bp = Blueprint('roster', __name__, url_prefix='/api/classes')

SESSION_KEY = 'mentor_id'  # must match the key used in profile.py / classes.py


def _class_belongs_to_mentor(class_id, mentor_id, conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM classes WHERE id = %s AND created_by = %s",
            (class_id, mentor_id)
        )
        return cur.fetchone() is not None


@roster_bp.route('/<int:class_id>/students', methods=['GET'])
def list_students(class_id):
    """GET /api/classes/<id>/students -> the roster for one of the mentor's classes."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            """SELECT s.id, s.fullname, s.email
               FROM student_classes sc
               JOIN student_signup s ON s.id = sc.student_id
               WHERE sc.class_id = %s
               ORDER BY s.fullname""",
            (class_id,)
        )
        rows = cur.fetchall()
    conn.close()

    students = [{"id": r[0], "fullname": r[1], "email": r[2]} for r in rows]
    return jsonify({"students": students}), 200


@roster_bp.route('/<int:class_id>/students', methods=['POST'])
def add_student(class_id):
    """POST /api/classes/<id>/students {email} -> enroll an existing student by email."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, fullname, email FROM student_signup WHERE email = %s",
            (email,)
        )
        student = cur.fetchone()

    if not student:
        conn.close()
        return jsonify({"error": "No student is registered with that email"}), 404

    student_id, fullname, student_email = student

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM student_classes WHERE class_id = %s AND student_id = %s",
            (class_id, student_id)
        )
        if cur.fetchone():
            conn.close()
            return jsonify({"error": "Student is already in this class"}), 409

        cur.execute(
            """INSERT INTO student_classes (class_id, student_id, added_by)
               VALUES (%s, %s, %s)""",
            (class_id, student_id, mentor_id)
        )
        conn.commit()
    conn.close()

    return jsonify({
        "message": "Student added",
        "student": {"id": student_id, "fullname": fullname, "email": student_email}
    }), 201


@roster_bp.route('/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
def remove_student(class_id, student_id):
    """DELETE /api/classes/<id>/students/<student_id> -> unenroll a student."""
    mentor_id = session.get(SESSION_KEY)
    if not mentor_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    if not _class_belongs_to_mentor(class_id, mentor_id, conn):
        conn.close()
        return jsonify({"error": "Class not found"}), 404

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM student_classes WHERE class_id = %s AND student_id = %s RETURNING id",
            (class_id, student_id)
        )
        deleted = cur.fetchone()
        conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"error": "Student not found in this class"}), 404

    return jsonify({"message": "Student removed"}), 200