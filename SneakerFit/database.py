import sqlite3
import os

DB_FILE = 'users.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    if not os.path.exists(DB_FILE):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                registration_date TEXT,
                registration_type TEXT,
                foot_length REAL,
                foot_width REAL,
                arch TEXT,
                oblique_circumference REAL,
                foot_type TEXT,
                avatar TEXT,
                about TEXT, 
                subscription INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
