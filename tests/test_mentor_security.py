import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MentorSecurityTests(unittest.TestCase):
    def test_protected_api_routes_have_onboarding_guard(self):
        expected = {
            "assignments.py": ["create_assignment", "list_assignments", "delete_assignment"],
            "attendance.py": ["get_attendance", "save_attendance"],
            "dashboard.py": ["dashboard_summary"],
            "marks.py": ["create_exam", "list_exams", "delete_exam", "get_marks", "save_marks"],
            "notes.py": ["create_note", "list_notes"],
            "roster.py": ["list_students", "add_student", "remove_student"],
            "timetable.py": ["create_slot", "list_slots", "delete_slot"],
        }

        for filename, functions in expected.items():
            tree = ast.parse((ROOT / "mentor" / "backend" / filename).read_text())
            found = {
                node.name: any(
                    isinstance(dec, ast.Name) and dec.id == "require_onboarding_complete"
                    for dec in node.decorator_list
                )
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for function_name in functions:
                self.assertTrue(
                    found.get(function_name, False),
                    f"{filename}:{function_name} is missing onboarding protection",
                )

    def test_onboarding_bootstrap_routes_remain_available(self):
        tree = ast.parse((ROOT / "mentor" / "backend" / "classes.py").read_text())
        create_class = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "create_class"
        )
        self.assertFalse(
            any(
                isinstance(dec, ast.Name) and dec.id == "require_onboarding_complete"
                for dec in create_class.decorator_list
            )
        )

    def test_production_security_configuration_is_present(self):
        app_source = (ROOT / "backend" / "app.py").read_text()
        config_source = (ROOT / "backend" / "config.py").read_text()
        self.assertIn("SESSION_COOKIE_HTTPONLY", app_source)
        self.assertIn("SESSION_COOKIE_SAMESITE", app_source)
        self.assertIn("X-Content-Type-Options", app_source)
        self.assertIn("Strict-Transport-Security", app_source)
        self.assertIn("debug=APP_ENV != \"production\"", app_source)
        self.assertIn("SECRET_KEY must be configured", config_source)

    def test_auth_endpoints_are_rate_limited(self):
        source = (ROOT / "backend" / "app.py").read_text()
        self.assertIn("from backend.security import auth_rate_limit", source)
        self.assertIn("@auth_rate_limit", source)

    def test_database_module_does_not_hard_code_credentials(self):
        source = (ROOT / "backend" / "db.py").read_text()
        self.assertNotIn('password="root"', source)
        self.assertNotIn('dbname="signup_user"', source)


if __name__ == "__main__":
    unittest.main()
