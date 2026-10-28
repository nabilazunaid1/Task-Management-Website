
import hmac
import secrets
from datetime import date

from flask import request, jsonify, session


def register_middleware(app):

    @app.before_request
    def validate_request():

        # Only apply these checks to API routes.
        if not request.path.startswith("/api/"):
            return

        # Protect private task endpoints.
        if request.path.startswith("/api/tasks"):
            if "user_id" not in session:
                return jsonify({
                    "error": "Please log in first"
                }), 401

        # Check a CSRF token for changes.
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            expected = session.get("csrf_token", "")
            received = request.headers.get("X-CSRF-Token", "")

            if not expected or not hmac.compare_digest(
                expected, received
            ):
                return jsonify({
                    "error": "Invalid security token. Refresh the page."
                }), 403

        
        # Logout does not need JSON data.
            if request.path == "/api/logout":
                return

        # Validate JSON for POST and PUT requests.
        if request.method not in ["POST", "PUT"]:
            return

        if not request.is_json:
            return jsonify({
                "error": "Please send JSON data"
            }), 400

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid JSON object"
            }), 400

        # Task-specific checks.
        if not request.path.startswith("/api/tasks"):
            return

        title = data.get("title")

        if not isinstance(title, str) or not title.strip():
            return jsonify({
                "error": "Task title cannot be empty"
            }), 400

        if len(title.strip()) > 100:
            return jsonify({
                "error": "Maximum title length is 100 characters"
            }), 400

        priority = data.get("priority", "Medium")

        if priority not in ["Low", "Medium", "High"]:
            return jsonify({
                "error": "Invalid priority"
            }), 400

        due_date = data.get("due_date")

        if due_date is not None:
            if not isinstance(due_date, str):
                return jsonify({
                    "error": "Invalid due date"
                }), 400

            try:
                parsed = date.fromisoformat(due_date)

                if parsed.isoformat() != due_date:
                    raise ValueError()

            except ValueError:
                return jsonify({
                    "error": "Invalid date format"
                }), 400

        if request.method == "PUT":
            if not isinstance(data.get("completed"), bool):
                return jsonify({
                    "error": "Completed must be true or false"
                }), 400
