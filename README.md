# Student Management

A Flask/PostgreSQL student and mentor management application.

## Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer
- Node.js 18 or newer (only needed for JavaScript syntax checks)

## Local setup

Create a PostgreSQL database and user, then copy the environment template:

```bash
createdb signup_user
cp .env.example .env
```

Edit `.env` with the PostgreSQL credentials and set a development secret:

```dotenv
SECRET_KEY=use-a-long-random-development-secret
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=signup_user
DB_USER=postgres
DB_PASSWORD=your-password
```

Install dependencies and apply the schema before starting Flask:

```bash
python3 -m pip install -r requirements.txt
psql "$DB_NAME" -f database/migrations/001_initial.sql
python3 -m backend.app
```

Open <http://127.0.0.1:5000/> in a browser.

The legacy `database/signup_user.sql` file is a `psql` entry point that delegates to the versioned initial migration. Future schema changes should be added as new numbered migration files and applied during deployment, not from request handlers.

## Tests

The security tests are database-independent. The integration tests require a reachable PostgreSQL database and apply the migration automatically before each test run:

```bash
python3 -m unittest discover -s tests -v
```

Run the complete local checks with:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
for file in $(find frontend mentor/frontend -name '*.js' -type f); do node --check "$file"; done
```

If PostgreSQL is unavailable, integration tests are reported as skipped; they are expected to run in CI, where the workflow starts a PostgreSQL service.

## Application flow

Students can sign up and log in to view classes, assignments, notes, timetable entries, attendance, exams, and marks. Mentors sign up with a mentor ID, complete profile onboarding, create classes, enroll students, and manage course content.
