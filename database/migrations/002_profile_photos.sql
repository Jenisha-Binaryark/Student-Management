BEGIN;

ALTER TABLE student_signup
    ADD COLUMN IF NOT EXISTS profile_photo TEXT;

ALTER TABLE mentor_signup
    ADD COLUMN IF NOT EXISTS profile_photo TEXT;

COMMIT;

