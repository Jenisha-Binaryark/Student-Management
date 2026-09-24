BEGIN;

CREATE TABLE IF NOT EXISTS student_signup (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    referral VARCHAR(120),
    profile_photo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mentor_signup (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    mentor_id VARCHAR(80) NOT NULL UNIQUE,
    referral VARCHAR(120),
    department VARCHAR(120),
    designation VARCHAR(120),
    profile_photo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    class_name VARCHAR(160) NOT NULL,
    university VARCHAR(160) NOT NULL,
    course VARCHAR(160) NOT NULL,
    year VARCHAR(40) NOT NULL,
    subject VARCHAR(160) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('mentor', 'teacher')),
    created_by INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_classes (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES student_signup(id) ON DELETE CASCADE,
    added_by INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (class_id, student_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES student_signup(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (class_id, student_id, date)
);

CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignment_submissions (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES student_signup(id) ON DELETE CASCADE,
    submission_text TEXT,
    submission_url TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (assignment_id, student_id),
    CHECK (submission_text IS NOT NULL OR submission_url IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS mentor_notes (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS class_timetable (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    day_of_week VARCHAR(3) NOT NULL CHECK (day_of_week IN ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')),
    subject VARCHAR(160) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(120),
    timetable_type VARCHAR(20) NOT NULL DEFAULT 'regular' CHECK (timetable_type IN ('regular', 'exam')),
    exam_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_time > start_time),
    CHECK (timetable_type = 'regular' OR exam_date IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    max_marks NUMERIC(10, 2) NOT NULL CHECK (max_marks > 0),
    exam_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marks (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES student_signup(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES mentor_signup(id) ON DELETE RESTRICT,
    score NUMERIC(10, 2) NOT NULL CHECK (score >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exam_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_classes_created_by ON classes(created_by);
CREATE INDEX IF NOT EXISTS idx_student_classes_student ON student_classes(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_assignments_class_due_date ON assignments(class_id, due_date);
CREATE INDEX IF NOT EXISTS idx_notes_class_created_at ON mentor_notes(class_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_timetable_class_day_time ON class_timetable(class_id, day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_exams_class_date ON exams(class_id, exam_date DESC);

COMMIT;
