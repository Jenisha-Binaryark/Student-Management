import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))

APP_ENV = os.getenv("APP_ENV", "development").lower()
SESSION_COOKIE_SECURE = os.getenv(
    "SESSION_COOKIE_SECURE",
    "1" if APP_ENV == "production" else "0",
) == "1"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
SESSION_LIFETIME_HOURS = int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
SESSION_LIFETIME = timedelta(hours=SESSION_LIFETIME_HOURS)

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be configured in the environment")

if APP_ENV == "production" and SECRET_KEY == "replace-with-a-long-random-secret":
    raise RuntimeError("A real SECRET_KEY is required in production")
