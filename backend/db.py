import psycopg2

from backend.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)
def get_db_connection():
    return psycopg2.connect(
        dbname="signup_user",
        user="postgres",
        password="root",
        host="localhost",
        port="5432"
    )