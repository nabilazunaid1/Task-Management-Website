
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasks.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# -----------------------------------
# Create and upgrade database tables
# -----------------------------------
def init_db():
    with get_connection() as connection:

        # Users table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        # Tasks table for brand-new installations
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'Medium',
                due_date TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Find columns in an existing Level 1/2 database.
        columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        ]

        if "priority" not in columns:
            connection.execute("""
                ALTER TABLE tasks
                ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'
            """)

        if "due_date" not in columns:
            connection.execute("""
                ALTER TABLE tasks
                ADD COLUMN due_date TEXT
            """)

        if "user_id" not in columns:
            connection.execute("""
                ALTER TABLE tasks
                ADD COLUMN user_id INTEGER
                REFERENCES users(id)
            """)


# -----------------------------------
# User account functions
# -----------------------------------
def create_user(email, password_hash):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        """, (email, password_hash))

        return cursor.lastrowid


def get_user_by_email(email):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,)).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT id, email FROM users WHERE id = ?
        """, (user_id,)).fetchone()

    return dict(row) if row else None


# -----------------------------------
# Task functions
# -----------------------------------
def get_tasks(user_id):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, title, completed, priority, due_date
            FROM tasks
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def get_task(task_id, user_id):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT id, title, completed, priority, due_date
            FROM tasks
            WHERE id = ? AND user_id = ?
        """, (task_id, user_id)).fetchone()

    return dict(row) if row else None


def create_task(user_id, title, priority, due_date):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO tasks
                (user_id, title, priority, due_date)
            VALUES (?, ?, ?, ?)
        """, (user_id, title, priority, due_date))

        task_id = cursor.lastrowid

    return get_task(task_id, user_id)


def update_task(
    task_id, user_id, title, completed, priority, due_date
):
    with get_connection() as connection:
        connection.execute("""
            UPDATE tasks
            SET title = ?,
                completed = ?,
                priority = ?,
                due_date = ?
            WHERE id = ? AND user_id = ?
        """, (
            title,
            int(completed),
            priority,
            due_date,
            task_id,
            user_id
        ))

    return get_task(task_id, user_id)


def delete_task(task_id, user_id):
    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM tasks
            WHERE id = ? AND user_id = ?
        """, (task_id, user_id))

    return cursor.rowcount > 0
