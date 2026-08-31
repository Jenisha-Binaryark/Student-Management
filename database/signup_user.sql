SELECT current_database();

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'signup_user';

SELECT * FROM signup_user;