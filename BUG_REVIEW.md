# Student Management Project — Bug Review

**Repository:** `Jenisha-Binaryark/Student-Management`  
**Branch reviewed:** `main`  
**Review date:** 2026-09-22  
**Working copy:** cloned locally from GitHub; no source files were modified during this review.

## Executive summary

The application is a Flask frontend/backend with PostgreSQL persistence and separate student and mentor flows. The source files compile, the JavaScript files pass Node syntax checks, and the five existing security-focused tests pass when invoked with the repository's CI command. However, a clean checkout is not currently reproducible: the only database file is a four-line inspection query, there is no README or startup guide, and the application expects a pre-existing PostgreSQL schema containing many tables that are never created by the repository.

The highest-probability reason the project appears “not working” on a new machine is therefore environment/database setup, followed by insufficient integration coverage. Several implementation choices can also cause production failures, especially schema changes being performed inside normal API requests.

## Verification performed

| Check | Result |
|---|---|
| Python compilation (`python -m compileall -q .`) | Passed |
| JavaScript syntax (`node --check` for every `.js`) | Passed |
| Existing tests (`python -m unittest discover -s tests -v`) | 5 passed |
| Default test command (`python -m unittest discover -v`) | Incorrectly reports `NO TESTS RAN` |
| Flask application import after installing `requirements.txt` | Passed |
| Flask route map inspection | Passed; routes register successfully |
| PostgreSQL-backed runtime flow | Not executable in this sandbox because no configured PostgreSQL instance/schema is available |

## Findings by priority

### P0 — Fresh installation has no database schema

**Evidence:** `database/signup_user.sql` contains only:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
SELECT * FROM classes;
```

The backend expects at least `student_signup`, `mentor_signup`, `classes`, `student_classes`, `attendance`, `assignments`, `assignment_submissions`, `mentor_notes`, `class_timetable`, `exams`, and `marks`. Most of these tables are referenced throughout `backend/` and `mentor/backend/`, but no `CREATE TABLE` migration or seed script is checked in.

**Impact:** A clean database cannot run signup, login, dashboards, classes, attendance, assignments, notes, timetable, exams, or marks. Requests will return the generic `Server error` response after PostgreSQL reports missing relations.

**Recommended fix:** Replace the inspection SQL file with versioned migrations (or a complete idempotent schema script), document how to create the database/user, and add a small seed dataset for local development.

### P0 — No setup or run documentation

**Evidence:** There is no `README.md`. The repository has `.env.example`, but no instructions explaining dependency installation, PostgreSQL setup, schema initialization, Flask startup, or the expected URL.

**Impact:** Contributors must infer the required environment. The current project can be cloned successfully but cannot be reliably started without external knowledge and a manually prepared database.

**Recommended fix:** Add a README with exact commands, required environment variables, migration/seed steps, startup command, test command, and troubleshooting for PostgreSQL connection errors.

### P1 — Database schema modifications happen during normal API requests

**Evidence:**

- `backend/student_content.py:6-22` creates `assignment_submissions` during requests.
- `backend/student_content.py:34-36` alters `class_timetable` during a student content request.
- `backend/student_dashboard.py:32-44` creates `assignment_submissions` during dashboard summary requests.
- `mentor/backend/dashboard.py:32-35` alters `class_timetable` during mentor dashboard requests.

**Impact:** Every affected request may require DDL privileges, acquire PostgreSQL locks, and fail in production when the application user is intentionally denied schema modification. Two separate request paths also duplicate migration logic. A first request can be slow or fail halfway through setup, producing inconsistent behavior.

**Recommended fix:** Move all table creation and `ALTER TABLE` statements into migrations executed once during deployment. Keep request handlers limited to reads/writes and make migrations explicit and versioned.

### P1 — The test suite does not exercise the application’s real failure points

**Evidence:** `tests/test_mentor_security.py` contains only AST/source-policy tests. It does not create a Flask test client, mock or provision PostgreSQL, test signup/login, test session handling, test student APIs, test mentor APIs, or test database error behavior.

The default command `python -m unittest discover -v` reports `NO TESTS RAN`; CI succeeds only because it supplies `-s tests`.

**Impact:** The checks can pass while the application is unable to connect to the database or while API queries reference missing tables/columns. Regressions in frontend/backend contracts will not be detected.

**Recommended fix:** Add Flask route tests with a test database or database adapter mock, API contract tests for both roles, and a CI PostgreSQL service initialized from migrations. Standardize the command in `Makefile`/README and make the default discovery command collect tests by adding `tests/__init__.py` or using `discover -s tests` consistently.

### P1 — Database errors are hidden behind generic responses

**Evidence:** `backend/app.py` catches broad `Exception` blocks in signup, login, and homework handlers, prints the exception, and returns only `{"status": "error", "message": "Server error"}`. Similar broad handling or uncaught database errors exist across feature blueprints.

**Impact:** Users see an unhelpful message such as “Server error” for missing tables, invalid schema, or connection failures. Operators have no structured logging or request context to diagnose the issue.

**Recommended fix:** Use application logging with stack traces and request identifiers, classify expected database errors, and expose safe, actionable messages in development while keeping production responses non-sensitive.

### P2 — The database configuration is mandatory even for routes that do not need the database

**Evidence:** `backend/config.py` raises if `SECRET_KEY` is missing, and `backend/db.py` validates all DB variables only when a DB connection is requested. The application imports all blueprints at startup, so the project still requires a correctly configured `SECRET_KEY` before even serving the landing page.

**Impact:** A new user who runs the app without copying `.env.example` receives an immediate startup exception rather than a clear setup message. This is expected security behavior for the secret, but the repository does not document it.

**Recommended fix:** Keep the strict production validation, add an explicit development configuration path or a clear startup error, and document required environment variables and safe local values.

### P2 — Authentication and authorization behavior is not integration-tested

**Evidence:** `backend/app.py` stores student and mentor identifiers in separate session keys and routes are split across multiple blueprints. Existing tests only inspect decorators in source code. There are no tests proving that a student cannot access mentor APIs, that an unauthenticated user receives the expected redirect/401 for every page/API, or that a mentor cannot access another mentor’s class data.

**Impact:** Security regressions can pass CI. The source-level decorator test verifies the presence of a decorator name, not its runtime behavior or data isolation.

**Recommended fix:** Add request-level authorization tests for both roles, including cross-tenant/class ownership cases and session transitions after logout/login.

### P2 — Frontend UX can mask API failures

**Evidence:** Most frontend scripts call `response.json()` and then update the page based on the returned payload. Because backend failures are represented inconsistently (`status`, `error`, redirects, and generic 500 responses), the client frequently falls back to generic “Could not load” messages. There is also no shared API error helper or visible database/setup diagnostic.

**Impact:** Users experience blank/empty dashboard sections instead of seeing which backend dependency failed.

**Recommended fix:** Standardize API responses and add a shared fetch wrapper that handles 401, 403, 429, and 5xx responses consistently.

## Recommended repair order

1. Add a complete, versioned PostgreSQL schema and seed data; remove request-time DDL.
2. Add README setup instructions and a single documented run/test workflow.
3. Add PostgreSQL-backed integration tests for signup, login, student dashboard/content, and mentor CRUD flows.
4. Add runtime authorization/data-isolation tests for both roles.
5. Improve structured logging and consistent API error responses.
6. Add frontend contract/error handling tests and improve user-facing diagnostics.

## Conclusion

The project is not failing because of syntax errors: the codebase passes compilation and basic source-policy checks. The dominant blocker is that the repository does not contain the database contract or the instructions needed to reproduce the application. Fixing schema setup and adding integration tests should come before chasing individual UI bugs, because the current test suite cannot currently distinguish a working feature from a database that was never initialized.

No changes were pushed to GitHub during this review.
