from database import get_connection

def user_exists(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_user(user_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users 
        (username, email, password, registration_date, registration_type, foot_length, foot_width, arch, oblique_circumference, foot_type, avatar, about, subscription)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_data.get('username', ''),
        user_data.get('email', ''),
        user_data.get('password', ''),
        user_data.get('registration_date', ''),
        user_data.get('registration_type', 'form'),
        user_data.get('subscription', 0),
        None, None, None, None, None, '', '', 0
    ))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_user_measurements(email, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET foot_length=?, foot_width=?, arch=?, oblique_circumference=?, foot_type=?
        WHERE email=?
    """, (
        data.get('length', None),
        data.get('width', None),
        data.get('arch', None),
        data.get('oblique_circumference', None),
        data.get('foot_type', None),
        email
    ))
    conn.commit()
    conn.close()

def update_user_profile(email, about=None, avatar_path=None):
    conn = get_connection()
    cursor = conn.cursor()
    if about is not None and avatar_path:
        cursor.execute("""
            UPDATE users
            SET about=?, avatar=?
            WHERE email=?
        """, (about, avatar_path, email))
    elif about is not None:
        cursor.execute("UPDATE users SET about=? WHERE email=?", (about, email))
    elif avatar_path:
        cursor.execute("UPDATE users SET avatar=? WHERE email=?", (avatar_path, email))
    conn.commit()
    conn.close()

def update_user_nickname(email, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username=? WHERE email=?", (new_name, email))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
