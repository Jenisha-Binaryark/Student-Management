import os
import pathlib
import unittest

import psycopg2

os.environ.setdefault("SECRET_KEY", "role-test-secret")
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


class RoleAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            connection = get_db_connection()
        except psycopg2.Error as exc:
            raise unittest.SkipTest(f"PostgreSQL is unavailable: {exc}") from exc
        with connection.cursor() as cur:
            cur.execute(MIGRATION.read_text())
        connection.commit()
        connection.close()

    def setUp(self):
        _attempts.clear()
        connection = get_db_connection()
        with connection.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE "
                "marks, exams, class_timetable, mentor_notes, "
                "assignment_submissions, assignments, attendance, "
                "student_classes, classes, mentor_signup, student_signup "
                "RESTART IDENTITY CASCADE"
            )
        connection.commit()
        connection.close()
        app.config.update(TESTING=True)

    @staticmethod
    def _signup_and_login(client, *, role, fullname, email, phone, password, mentor_id=None):
        payload = {
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "password": password,
            "role": role,
        }
        if mentor_id:
            payload["mentorId"] = mentor_id
        signup = client.post("/signup", json=payload)
        if signup.get_json().get("status") != "created":
            raise AssertionError(signup.get_json())
        login = client.post(
            "/login",
            json={"username": email, "password": password, "role": role},
        )
        if login.get_json().get("status") != "success":
            raise AssertionError(login.get_json())

    def test_student_session_cannot_access_mentor_pages_or_apis(self):
        student = app.test_client()
        self._signup_and_login(
            student,
            role="student",
            fullname="Role Student",
            email="role.student@example.com",
            phone="9000000011",
            password="StrongRole1!",
        )

        for path in (
            "/mentor/dashboard.html", "/mentor/onboarding.html", "/mentor/grades.html",
            "/mentor/schedule.html", "/mentor/messages.html", "/mentor/settings.html",
        ):
            with self.subTest(path=path):
                response = student.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login.html?role=mentor", response.headers["Location"])

        response = student.get("/mentor/sidebar.html")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["status"], "not_logged_in")

        for path in ("/api/profile/status", "/api/classes", "/api/dashboard/summary"):
            with self.subTest(path=path):
                response = student.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.get_json()["error"], "Unauthorized")

        for path in (
            "/dashboard.html", "/homework.html", "/my_classes.html",
            "/grades.html", "/schedule.html", "/messages.html", "/settings.html",
        ):
            with self.subTest(path=path):
                self.assertEqual(student.get(path).status_code, 200)
        self.assertEqual(student.get("/api/student/content").status_code, 200)
        self.assertEqual(student.get("/api/student/profile").status_code, 200)

    def test_mentor_session_cannot_access_student_pages_or_apis(self):
        mentor = app.test_client()
        self._signup_and_login(
            mentor,
            role="mentor",
            fullname="Role Mentor",
            email="role.mentor@example.com",
            phone="9000000012",
            password="StrongRole2!",
            mentor_id="ROLE-M-001",
        )

        for path in (
            "/dashboard.html", "/homework.html", "/my_classes.html",
            "/grades.html", "/schedule.html", "/messages.html", "/settings.html",
            "/sidebar.html",
        ):
            with self.subTest(path=path):
                response = mentor.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login.html?role=student", response.headers["Location"])

        for path in ("/api/student/content", "/api/student/dashboard/summary", "/api/student/profile"):
            with self.subTest(path=path):
                response = mentor.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.get_json()["error"], "Unauthorized")

        self.assertEqual(mentor.get("/mentor/onboarding.html").status_code, 200)
        for path in (
            "/mentor/dashboard.html", "/mentor/grades.html", "/mentor/schedule.html",
            "/mentor/messages.html", "/mentor/settings.html",
        ):
            response = mentor.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/mentor/onboarding.html", response.headers["Location"])
        self.assertEqual(mentor.get("/api/profile/status").status_code, 200)
        self.assertEqual(mentor.get("/api/profile/details").status_code, 200)

    def test_unauthenticated_requests_are_redirected_to_the_correct_login_role(self):
        client = app.test_client()

        for path, expected_role in (
            ("/dashboard.html", "student"),
            ("/homework.html", "student"),
            ("/grades.html", "student"),
            ("/schedule.html", "student"),
            ("/messages.html", "student"),
            ("/settings.html", "student"),
            ("/mentor/dashboard.html", "mentor"),
            ("/mentor/onboarding.html", "mentor"),
            ("/mentor/grades.html", "mentor"),
            ("/mentor/schedule.html", "mentor"),
            ("/mentor/messages.html", "mentor"),
            ("/mentor/settings.html", "mentor"),
        ):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn(f"/login.html?role={expected_role}", response.headers["Location"])

        for path in ("/api/student/content", "/api/student/dashboard/summary", "/api/classes", "/api/dashboard/summary"):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 401)


if __name__ == "__main__":
    unittest.main()
