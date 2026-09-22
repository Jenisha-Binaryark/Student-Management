from functools import wraps
from flask import session, jsonify
from backend.db import get_db_connection
from mentor.backend.profile import get_onboarding_status, SESSION_KEY


def require_onboarding_complete(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mentor_id = session.get(SESSION_KEY)
        if session.get("role") != "mentor" or not mentor_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        try:
            status = get_onboarding_status(mentor_id, conn)
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if not status["all_complete"]:
            return jsonify({
                "error": "Onboarding incomplete",
                "onboarding": status
            }), 403

        return f(*args, **kwargs)

    return wrapper
