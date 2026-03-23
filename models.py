from flask import g
from flask_login import UserMixin
import sqlite3
from pathlib import Path

DB_PATH = Path("petlift.db")

class User(UserMixin):
    def __init__(self, user_id, name, email, role):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport_requests (
            request_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            rescuer_id     INTEGER NOT NULL,
            pickup_loc     TEXT NOT NULL,
            dropoff_clinic TEXT NOT NULL,
            crate_count    INTEGER NOT NULL,
            reason         TEXT,
            status         TEXT NOT NULL DEFAULT 'open',
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            driver_id  INTEGER NOT NULL,
            status     TEXT NOT NULL DEFAULT 'scheduled'
        );
    """)
    db.commit()
    db.close()

def get_user_by_email(email):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    )
    row = cur.fetchone()
    db.close()
    if row:
        return User(row["user_id"], row["name"], row["email"], row["role"])
    return None

def get_user_by_id(user_id):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    row = cur.fetchone()
    db.close()
    if row:
        return User(row["user_id"], row["name"], row["email"], row["role"])
    return None
    