-- Compatibility entry point for existing local setup commands.
-- Run: psql signup_user -f database/signup_user.sql
\ir migrations/001_initial.sql
\ir migrations/002_profile_photos.sql
