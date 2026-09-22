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

    def test_mentor_dashboard_prevents_card_stretching(self):
        css = (ROOT / "mentor" / "frontend" / "styles" / "dashboard.css").read_text()
        self.assertIn("grid-auto-rows:max-content", css)
        self.assertIn(".grid > .stats-col", css)
        self.assertIn("grid-row:1 / span 2", css)
        self.assertIn("min-height:104px", css)

    def test_student_dashboard_has_complete_layout_rules(self):
        css = (ROOT / "frontend" / "styles" / "dashboard.css").read_text()
        self.assertIn("grid-auto-rows:max-content", css)
        self.assertIn(".stats-col{grid-column:2;grid-row:1 / span 3", css)
        self.assertIn(".schedule-row{grid-column:1 / -1", css)
        self.assertIn("@media(max-width:700px)", css)

    def test_student_classes_loads_shared_navigation(self):
        html = (ROOT / "frontend" / "my_classes.html").read_text()
        script = (ROOT / "frontend" / "src" / "my_classes.js").read_text()
        css = (ROOT / "frontend" / "styles" / "my_classes.css").read_text()
        self.assertIn("styles/sidebar.css", html)
        self.assertIn("loadSidebar", script)
        self.assertIn(".classes-section", css)

    def test_homework_does_not_clip_page_content(self):
        css = (ROOT / "frontend" / "styles" / "homework.css").read_text()
        self.assertIn("min-height:100vh", css)
        self.assertNotIn(".homework{height:100vh", css)
        self.assertNotIn("overflow:hidden", css)

    def test_student_motion_polish_has_reduced_motion_fallback(self):
        sidebar = (ROOT / "frontend" / "styles" / "sidebar.css").read_text()
        dashboard = (ROOT / "frontend" / "styles" / "dashboard.css").read_text()
        self.assertIn("@keyframes studentSidebarIn", sidebar)
        self.assertIn("prefers-reduced-motion:reduce", sidebar)
        self.assertIn("@keyframes studentContentIn", dashboard)

    def test_mentor_motion_polish_has_reduced_motion_fallback(self):
        sidebar = (ROOT / "mentor" / "frontend" / "styles" / "mentor_sidebar.css").read_text()
        self.assertIn("@keyframes mentorSidebarIn", sidebar)
        self.assertIn("@keyframes mentorModalIn", sidebar)
        self.assertIn("prefers-reduced-motion:reduce", sidebar)


if __name__ == "__main__":
    unittest.main()
