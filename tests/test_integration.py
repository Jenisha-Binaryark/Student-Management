import os
import pathlib
import unittest

import psycopg2

os.environ.setdefault("SECRET_KEY", "integration-test-secret")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "signup_user")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")

from backend.app import app
from backend.db import get_db_connection
from backend.security import _attempts


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "001_initial.sql"


class ApplicationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.connection = get_db_connection()
        except psycopg2.Error as exc:
            raise unittest.SkipTest(f"PostgreSQL is unavailable: {exc}") from exc

        with cls.connection.cursor() as cur:
            cur.execute(MIGRATION.read_text())
        cls.connection.commit()
        cls.connection.close()

    def setUp(self):
        _attempts.clear()
        self.connection = get_db_connection()
        with self.connection.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE "
                "marks, exams, class_timetable, mentor_notes, "
                "assignment_submissions, assignments, attendance, "
                "student_classes, classes, mentor_signup, student_signup "
                "RESTART IDENTITY CASCADE"
            )
        self.connection.commit()
        self.connection.close()
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def test_authentication_and_onboarding_flow(self):
        client = app.test_client()

        response = client.post(
            "/signup",
            json={
                "fullname": "Mentor One",
                "email": "mentor@example.com",
                "phone": "9000000001",
                "password": "StrongPass1!",
                "role": "mentor",
                "mentorId": "M-001",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "created")

        response = client.post(
            "/login",
            json={
                "username": "mentor@example.com",
                "password": "StrongPass1!",
                "role": "mentor",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["role"], "mentor")

        response = client.get("/api/profile/status")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["all_complete"])

        response = client.post(
            "/api/profile/complete",
            json={"department": "Computer Science", "designation": "Lecturer"},
        )
        self.assertEqual(response.status_code, 200)

        response = client.post(
            "/api/classes",
            json={
                "class_name": "CS-A",
                "university": "Example University",
                "course": "BSc Computer Science",
                "year": "2026",
                "subject": "Databases",
                "role": "mentor",
            },
        )
        self.assertEqual(response.status_code, 201)
        class_id = response.get_json()["class_id"]

        response = client.get("/api/profile/status")
        self.assertTrue(response.get_json()["all_complete"])

        response = client.get("/api/classes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["classes"][0]["id"], class_id)

    def test_student_and_mentor_coursework_flow(self):
        mentor = app.test_client()
        student = app.test_client()

        mentor.post(
            "/signup",
            json={
                "fullname": "Mentor Two",
                "email": "mentor2@example.com",
                "phone": "9000000002",
                "password": "StrongPass2!",
                "role": "mentor",
                "mentorId": "M-002",
            },
        )
        mentor.post(
            "/login",
            json={
                "username": "mentor2@example.com",
                "password": "StrongPass2!",
                "role": "mentor",
            },
        )
        mentor.post(
            "/api/profile/complete",
            json={"department": "Science", "designation": "Teacher"},
        )
        class_response = mentor.post(
            "/api/classes",
            json={
                "class_name": "BIO-A",
                "university": "Example University",
                "course": "BSc Biology",
                "year": "2026",
                "subject": "Biology",
                "role": "teacher",
            },
        )
        self.assertEqual(class_response.status_code, 201)
        class_id = class_response.get_json()["class_id"]

        student.post(
            "/signup",
            json={
                "fullname": "Student One",
                "email": "student@example.com",
                "phone": "9000000003",
                "password": "StrongPass3!",
                "role": "student",
            },
        )
        student.post(
            "/login",
            json={
                "username": "student@example.com",
                "password": "StrongPass3!",
                "role": "student",
            },
        )
        self.assertEqual(student.get("/api/student/content").status_code, 200)

        response = mentor.post(
            f"/api/classes/{class_id}/students",
            json={"email": "student@example.com"},
        )
        self.assertEqual(response.status_code, 201)

        response = mentor.post(
            "/api/assignments",
            json={
                "class_id": class_id,
                "title": "Lab report",
                "description": "Submit the report",
                "due_date": "2026-10-01",
            },
        )
        self.assertEqual(response.status_code, 201)
        assignment_id = response.get_json()["assignment"]["id"]

        response = student.post(
            f"/api/student/assignments/{assignment_id}/submission",
            json={"text": "Completed report"},
        )
        self.assertEqual(response.status_code, 200)

        response = mentor.get(f"/api/assignments/{assignment_id}/submissions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["submissions"]), 1)

        response = mentor.post(
            "/api/attendance",
            json={
                "class_id": class_id,
                "date": "2026-09-22",
                "records": [{"student_id": 1, "status": "present"}],
            },
        )
        self.assertEqual(response.status_code, 200)

        response = mentor.post(
            "/api/exams",
            json={
                "class_id": class_id,
                "title": "Midterm",
                "max_marks": 100,
                "exam_date": "2026-10-05",
            },
        )
        self.assertEqual(response.status_code, 201)
        exam_id = response.get_json()["exam"]["id"]

        response = mentor.post(
            "/api/marks",
            json={"exam_id": exam_id, "records": [{"student_id": 1, "score": 88}]},
        )
        self.assertEqual(response.status_code, 200)

        response = student.get("/api/student/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["attendance"]["percent"], 100)
        self.assertEqual(body["performance"]["percent"], 88)
        self.assertEqual(body["homework"]["percent"], 100)

    def test_mentor_cannot_access_another_mentors_class(self):
        client = app.test_client()
        for email, phone, mentor_id in [
            ("owner@example.com", "9000000004", "M-004"),
            ("other@example.com", "9000000005", "M-005"),
        ]:
            client.post(
                "/signup",
                json={
                    "fullname": mentor_id,
                    "email": email,
                    "phone": phone,
                    "password": "StrongPass4!",
                    "role": "mentor",
                    "mentorId": mentor_id,
                },
            )
            client.post(
                "/login",
                json={"username": email, "password": "StrongPass4!", "role": "mentor"},
            )
            client.post(
                "/api/profile/complete",
                json={"department": "Engineering", "designation": "Teacher"},
            )
            class_response = client.post(
                "/api/classes",
                json={
                    "class_name": mentor_id,
                    "university": "Example University",
                    "course": "Engineering",
                    "year": "2026",
                    "subject": "Testing",
                    "role": "mentor",
                },
            )
            if mentor_id == "M-004":
                owned_class_id = class_response.get_json()["class_id"]
            client.post("/logout")

        client.post(
            "/login",
            json={"username": "other@example.com", "password": "StrongPass4!", "role": "mentor"},
        )
        response = client.get(f"/api/assignments?class_id={owned_class_id}")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
