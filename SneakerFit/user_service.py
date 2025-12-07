from database import get_connection


def user_exists(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None
        return exists
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False
    finally:
        conn.close()


def save_user(user_data):
    """Существующая функция - оставляем для обратной совместимости"""
    return save_user_with_verification(user_data)


def save_user_with_verification(user_data):
    """Сохраняет пользователя с неподтвержденным email"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        print(f"Attempting to save user with verification: {user_data.get('username')}, {user_data.get('email')}")

        cursor.execute("""
            INSERT INTO users 
            (username, email, password, registration_date, registration_type, subscription,
             foot_length, foot_width, arch, oblique_circumference, foot_type, avatar, about, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.get('username', ''),
            user_data.get('email', ''),
            user_data.get('password', ''),
            user_data.get('registration_date', ''),
            user_data.get('registration_type', 'form'),
            0,  # subscription
            None,  # foot_length
            None,  # foot_width
            None,  # arch
            None,  # oblique_circumference
            None,  # foot_type
            None,  # avatar
            '',  # about
            False  # email_verified
        ))
        conn.commit()
        print(f"User {user_data.get('email')} saved with unverified email")
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_user_email(email):
    """Подтверждает email пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET email_verified = ?
            WHERE email = ?
        """, (True, email))
        conn.commit()
        print(f"Email verified for user: {email}")
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error verifying email: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def is_email_verified(email):
    """Проверяет, подтвержден ли email"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email_verified FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return row and row['email_verified'] == 1
    except Exception as e:
        print(f"Error checking email verification: {e}")
        return False
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None
    finally:
        conn.close()


def update_user_measurements(email, data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        print(f"Measurements updated for user: {email}")
        return True
    except Exception as e:
        print(f"Error updating user measurements: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_user_profile(email, about=None, avatar_path=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        print(f"Profile updated for user: {email}")
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_user_nickname(email, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET username=? WHERE email=?", (new_name, email))
        conn.commit()
        print(f"Nickname updated for user: {email} -> {new_name}")
        return True
    except Exception as e:
        print(f"Error updating user nickname: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        conn.close()