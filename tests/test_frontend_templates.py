import os
import pathlib
import unittest

os.environ.setdefault("SECRET_KEY", "frontend-test-secret")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "signup_user")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")

from flask import render_template

from backend.app import app


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FrontendTemplateTests(unittest.TestCase):
    def test_student_templates_use_normalized_static_urls(self):
        with app.test_request_context():
            for template in ("signup.html", "login.html", "dashboard.html"):
                html = render_template(template)
                self.assertNotIn("/frontend//", html, template)
                self.assertNotIn("filename='/'", html, template)

    def test_mentor_templates_use_mentor_dashboard_styles(self):
        with app.test_request_context():
            for template in (
                "mentor_dashboard.html",
                "attendance.html",
                "timetable.html",
                "assignments.html",
                "marks.html",
                "notes.html",
            ):
                html = render_template(template)
                self.assertIn("/mentor/static/styles/dashboard.css", html, template)
                self.assertIn("/frontend/styles/sidebar.css", html, template)
                self.assertIn("/mentor/static/styles/mentor_sidebar.css", html, template)

    def test_shared_sidebar_contains_navigation_base_rules(self):
        css = (ROOT / "frontend" / "styles" / "sidebar.css").read_text()
        self.assertIn(".sidebar nav ul", css)
        self.assertIn("display:flex", css)
        self.assertIn("text-decoration:none", css)
        self.assertIn(".logout", css)


if __name__ == "__main__":
    unittest.main()
