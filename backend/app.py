
import os
import secrets
import sqlite3
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from flask import (
    Flask, request, jsonify,
    session, send_from_directory
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_tasks,
    get_task,
    create_task,
    update_task,
    delete_task
)

from middleware import register_middleware


# ---------------------------------------
# Configuration
# ---------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")

if not secret_key or len(secret_key) < 32:
    raise RuntimeError(
        "Set a long random SECRET_KEY in your .env file"
    )

app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",

    # False for local HTTP. Use True for production HTTPS.
    SESSION_COOKIE_SECURE=False,

    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)

register_middleware(app)
init_db()


def new_session(user_id=None):
    """Start a fresh session and security token."""
    session.clear()

    if user_id is not None:
        session["user_id"] = user_id

    session["csrf_token"] = secrets.token_urlsafe(32)
    session.permanent = True

    return session["csrf_token"]


def current_user():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    return get_user_by_id(user_id)


# ---------------------------------------
# Frontend
# ---------------------------------------
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------
# Current logged-in user
# ---------------------------------------
@app.route("/api/me", methods=["GET"])
def me():
    user = current_user()

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return jsonify({
        "user": user,
        "csrf_token": session["csrf_token"]
    })


# ---------------------------------------
# Register
# ---------------------------------------
@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str):
        return jsonify({"error": "Email is required"}), 400

    email = email.strip().lower()

    if (
        len(email) > 254
        or "@" not in email
        or not email.split("@")[0]
        or "." not in email.split("@")[-1]
    ):
        return jsonify({"error": "Invalid email address"}), 400

    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return jsonify({
            "error": "Password must be 12 to 128 characters"
        }), 400

    password_hash = generate_password_hash(password)

    try:
        create_user(email, password_hash)

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "This email is already registered"
        }), 409

    return jsonify({
        "message": "Account created. Please log in."
    }), 201


# ---------------------------------------
# Login
# ---------------------------------------
@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    user = get_user_by_email(email.strip().lower())

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    token = new_session(user["id"])

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "email": user["email"]
        },
        "csrf_token": token
    })


# ---------------------------------------
# Logout
# ---------------------------------------
@app.route("/api/logout", methods=["POST"])
def logout():
    token = new_session()

    return jsonify({
        "message": "Logged out",
        "csrf_token": token
    })


# ---------------------------------------
# Private task APIs
# ---------------------------------------
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    return jsonify(get_tasks(session["user_id"]))


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def read_task(task_id):
    task = get_task(task_id, session["user_id"])

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task)


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json()

    task = create_task(
        user_id=session["user_id"],
        title=data["title"].strip(),
        priority=data.get("priority", "Medium"),
        due_date=data.get("due_date")
    )

    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def edit_task(task_id):
    user_id = session["user_id"]

    existing = get_task(task_id, user_id)

    if existing is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()

    task = update_task(
        task_id=task_id,
        user_id=user_id,
        title=data["title"].strip(),
        completed=data["completed"],
        priority=data.get("priority", "Medium"),
        due_date=data.get("due_date")
    )

    return jsonify(task)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def remove_task(task_id):
    deleted = delete_task(task_id, session["user_id"])

    if not deleted:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted"})


if __name__ == "__main__":
    app.run(debug=True)
