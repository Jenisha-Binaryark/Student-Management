import time
from collections import defaultdict, deque
from functools import wraps

from flask import jsonify, request

_WINDOW_SECONDS = 10 * 60
_MAX_REQUESTS = 10
_attempts = defaultdict(deque)


def auth_rate_limit(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        now = time.monotonic()
        key = request.remote_addr or "unknown"
        attempts = _attempts[key]
        while attempts and now - attempts[0] > _WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= _MAX_REQUESTS:
            return jsonify({
                "status": "error",
                "message": "Too many attempts. Please try again later."
            }), 429
        attempts.append(now)
        return view(*args, **kwargs)

    return wrapped
