from flask import g
import sqlite3
from pathlib import Path

DB_PATH = Path("petlift.db")

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
            email       TEXT UNIQUE,
            role        TEXT NOT NULL,
            has_vehicle INTEGER NOT NULL DEFAULT 0
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
    