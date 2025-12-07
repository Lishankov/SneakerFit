import os
import sqlite3


def reset_database():
    # Удаляем старую базу
    if os.path.exists('users.db'):
        os.remove('users.db')
        print("Old database removed")

    # Создаем новую
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            registration_date TEXT,
            registration_type TEXT,
            subscription INTEGER DEFAULT 0,
            foot_length REAL,
            foot_width REAL,
            arch TEXT,
            oblique_circumference REAL,
            foot_type TEXT,
            avatar TEXT,
            about TEXT DEFAULT '',
            email_verified BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    conn.close()
    print("New database created successfully")


if __name__ == "__main__":
    reset_database()