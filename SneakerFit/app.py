from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import datetime
import os
import re
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-123456789'

USERS_FILE = 'users.txt'
AVATARS_DIR = os.path.join('static', 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}


# -------------------------
# Utilities: users handling
# -------------------------
def ensure_storage():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            f.write('')
    if not os.path.exists(AVATARS_DIR):
        os.makedirs(AVATARS_DIR, exist_ok=True)


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def load_users():
    users = []
    if not os.path.exists(USERS_FILE):
        return users
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split(' | ')
            # Ensure at least 12 fields (pad if older lines)
            while len(parts) < 12:
                parts.append('')
            users.append(parts)
    return users


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        for u in users:
            f.write(' | '.join(u) + '\n')


def user_exists(email):
    for u in load_users():
        if u[1] == email:
            return True
    return False


def get_user_by_email(email):
    for u in load_users():
        if u[1] == email:
            return {
                'username': u[0],
                'email': u[1],
                'password': u[2],
                'registration_date': u[3],
                'registration_type': u[4],
                'foot_length': u[5],
                'foot_width': u[6],
                'arch': u[7],
                'dominant': u[8],
                'foot_type': u[9],
                'avatar': u[10],
                'about': u[11]
            }
    return None


def save_user(user_data):
    users = load_users()
    # append with placeholders for measurement/avatar/about
    users.append([
        user_data.get('username', ''),
        user_data.get('email', ''),
        user_data.get('password', ''),
        user_data.get('registration_date', ''),
        user_data.get('registration_type', 'form'),
        '', '', '', '', '',  # 5..9 measurement fields
        '',  # avatar (index 10)
        ''   # about (index 11)
    ])
    save_users(users)
    return True


def update_user_measurements(email, data):
    users = load_users()
    changed = False
    for u in users:
        if u[1] == email:
            u[5] = data.get('length', '') or ''
            u[6] = data.get('width', '') or ''
            u[7] = data.get('arch', '') or ''
            u[8] = data.get('dominant', '') or ''
            u[9] = data.get('foot_type', '') or ''
            changed = True
    if changed:
        save_users(users)


def update_user_profile(email, about=None, avatar_path=None):
    """
    If avatar_path provided: set path and delete previous avatar file (if exists and inside avatars dir).
    """
    users = load_users()
    for u in users:
        if u[1] == email:
            # avatar deletion: if new avatar uploaded, remove old file
            old_avatar = u[10]
            if avatar_path:
                # remove old avatar file if exists and path is inside avatars dir
                if old_avatar:
                    old_path = os.path.join(old_avatar.replace('/', os.sep))  # convert to path
                    # old_path may be like static/avatars/xxx.png
                    if os.path.exists(old_path) and os.path.commonpath([os.path.abspath(old_path), os.path.abspath(AVATARS_DIR)]) == os.path.abspath(AVATARS_DIR):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                # set new avatar path (web path)
                u[10] = avatar_path
            if about is not None:
                u[11] = about
    save_users(users)


def setup():
    ensure_storage()

setup()



@app.route('/')
def first():
    return render_template('first_page.html')


@app.route('/loggin')
def index():
    # login/register page
    if session.get('user_logged_in'):
        return redirect('/welcome')
    return render_template('register.html')


@app.route('/quick_login')
def quick_login():
    # demo quick login (creates demo user if not exists)
    demo_email = 'demo@example.com'
    if not user_exists(demo_email):
        save_user({
            'username': 'Демо Пользователь',
            'email': demo_email,
            'password': 'demo123',
            'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'registration_type': 'demo'
        })
    session['user_logged_in'] = True
    session['user_email'] = demo_email
    session['user_name'] = 'Демо Пользователь'
    return redirect('/welcome')


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Все поля обязательны'})
    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Имя слишком короткое'})
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Неверный email'})
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})

    if user_exists(email):
        return jsonify({'success': False, 'message': 'Пользователь уже существует'})

    save_user({
        'username': username,
        'email': email,
        'password': password,
        'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'registration_type': 'form'
    })

    session['user_logged_in'] = True
    session['user_email'] = email
    session['user_name'] = username

    return jsonify({'success': True, 'message': 'Регистрация успешна', 'redirect': '/welcome'})


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not email or not password:
        return jsonify({'success': False, 'message': 'Введите email и пароль'})

    user = get_user_by_email(email)
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})

    if user['password'] != password:
        return jsonify({'success': False, 'message': 'Неверный пароль'})

    session['user_logged_in'] = True
    session['user_email'] = email
    session['user_name'] = user['username']

    return jsonify({'success': True, 'message': 'Вход успешен', 'redirect': '/welcome'})


@app.route('/welcome')
def welcome():
    if not session.get('user_logged_in'):
        return redirect('/')
    user = get_user_by_email(session.get('user_email'))
    return render_template('welcome.html', username=user['username'], email=user['email'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/profile')
def profile():
    if not session.get('user_logged_in'):
        return redirect('/loggin')
    user = get_user_by_email(session.get('user_email'))
    return render_template('profile.html', user=user)


@app.route('/profile_update', methods=['POST'])
def profile_update():
    # update about text and optionally avatar upload
    if not session.get('user_logged_in'):
        return redirect('/loggin')
    email = session.get('user_email')
    about = request.form.get('about', '').strip()

    # handle avatar file
    file = request.files.get('avatar')
    avatar_web_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            return "Неподдерживаемый формат изображения", 400

        ensure_storage()
        # generate unique filename
        unique = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_name = f"{session.get('user_email').split('@')[0]}_{unique}.{ext}"
        save_path = os.path.join(AVATARS_DIR, new_name)
        file.save(save_path)
        avatar_web_path = os.path.join('static', 'avatars', new_name).replace('\\', '/')

    # update
    update_user_profile(email, about=about if about != '' else '', avatar_path=avatar_web_path)
    return redirect('/profile')

@app.route('/nickname_update', methods=['POST'])
def nickname_update():
    if not session.get('user_logged_in'):
        return redirect('/loggin')

    new_name = request.form.get('new_nickname', '').strip()
    email = session.get('user_email')

    # проверки
    if len(new_name) < 3:
        return "Имя слишком короткое"

    users = load_users()
    # проверка уникальности
    for u in users:
        if u[0] == new_name:
            return "Такой ник уже существует"

    # обновление
    for u in users:
        if u[1] == email:
            u[0] = new_name

    save_users(users)
    session['user_name'] = new_name

    return redirect('/profile')


@app.route('/measure', methods=['GET', 'POST'])
def measure():
    if not session.get('user_logged_in'):
        return redirect('/loggin')

    if request.method == 'POST':
        length = request.form.get('length', '').strip()
        width = request.form.get('width', '').strip()
        arch = request.form.get('arch', '').strip()
        dominant = request.form.get('dominant', '').strip()
        foot_type = request.form.get('foot_type', '').strip()

        update_user_measurements(session.get('user_email'), {
            'length': length,
            'width': width,
            'arch': arch,
            'dominant': dominant,
            'foot_type': foot_type
        })
        return redirect('/profile')

    return render_template('measure.html')


# -------------------------
# Admin-ish: view users (keeps previous simple table)
# -------------------------
@app.route('/users')
def view_users():
    if not os.path.exists(USERS_FILE):
        return "Пользователей пока нет"

    users = load_users()
    # generate simple html table
    html = """
    <!doctype html><html><head><meta charset="utf-8"><title>Users</title></head><body>
    <h1>Пользователи</h1>
    <table border="1" cellspacing="0" cellpadding="6">
    <tr><th>Имя</th><th>Email</th><th>Пароль</th><th>Дата</th><th>Тип</th><th>Length</th><th>Width</th><th>Arch</th><th>Dominant</th><th>Type</th><th>Avatar</th><th>About</th></tr>
    """
    for u in users:
        html += "<tr>"
        for col in u:
            html += f"<td>{col}</td>"
        html += "</tr>"
    html += "</table><br><a href='/'>← На главную</a></body></html>"
    return html


if __name__ == '__main__':
    ensure_storage()
    app.run(debug=True, host='0.0.0.0', port=5000)
