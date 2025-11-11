from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import datetime
import os
import re
from werkzeug.utils import secure_filename
import shutil
import json
import math
import random

def load_shoes_database():
    try:
        with open('base_of_shoes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"sneakers": []}


def calculate_compatibility(user_data, shoe_size):
    compatibility = 0
    factors = 0

    has_length = user_data.get('foot_length') and user_data['foot_length'].strip()
    has_width = user_data.get('foot_width') and user_data['foot_width'].strip()
    has_oblique = user_data.get('oblique_circumference') and user_data['oblique_circumference'].strip()
    has_foot_type = user_data.get('foot_type') and user_data['foot_type'].strip()

    if has_length:
        try:
            user_length = float(user_data['foot_length']) * 10
            shoe_length = shoe_size['length']
            length_diff = abs(user_length - shoe_length)

            if length_diff <= 3:
                length_score = 45
            elif length_diff <= 7:
                length_score = 40
            elif length_diff <= 12:
                length_score = 35
            elif length_diff <= 17:
                length_score = 25
            elif length_diff <= 22:
                length_score = 15
            else:
                length_score = 5

            compatibility += length_score
            factors += 45

        except ValueError:
            print("Ошибка преобразования длины")

    if has_width:
        try:
            user_width = float(user_data['foot_width']) * 10

            estimated_midfoot = 2 * (user_width + 50) * 0.9
            shoe_midfoot = shoe_size['midfootCircumference']
            width_diff = abs(estimated_midfoot - shoe_midfoot)

            if width_diff <= 15:
                width_score = 35
            elif width_diff <= 25:
                width_score = 30
            elif width_diff <= 35:
                width_score = 25
            elif width_diff <= 45:
                width_score = 18
            elif width_diff <= 55:
                width_score = 10
            else:
                width_score = 5

            compatibility += width_score
            factors += 35

        except ValueError:
            print("Ошибка преобразования ширины")

    if has_oblique:
        try:
            user_oblique = float(user_data['oblique_circumference']) * 10  # конвертируем см в мм
            shoe_oblique = shoe_size['obliqueCircumference']
            oblique_diff = abs(user_oblique - shoe_oblique)

            if oblique_diff <= 10:
                oblique_score = 15
            elif oblique_diff <= 20:
                oblique_score = 12
            elif oblique_diff <= 30:
                oblique_score = 8
            elif oblique_diff <= 40:
                oblique_score = 5
            else:
                oblique_score = 2

            compatibility += oblique_score
            factors += 15

        except ValueError:
            print("Ошибка преобразования косого обхвата")

    if has_foot_type:
        foot_type = user_data['foot_type']

        if foot_type == 'Плоскостопие':
            ankle_circ = shoe_size['ankleCircumference']
            midfoot_circ = shoe_size['midfootCircumference']

            if ankle_circ > 240 and midfoot_circ > 220:
                foot_type_score = 5
            elif ankle_circ > 230 and midfoot_circ > 210:
                foot_type_score = 3
            else:
                foot_type_score = 1

        elif foot_type == 'Супинация':
            toe_circ = shoe_size['toeCircumference']
            if toe_circ > 240:
                foot_type_score = 5
            elif toe_circ > 220:
                foot_type_score = 3
            else:
                foot_type_score = 1

        else:
            foot_type_score = 4

        compatibility += foot_type_score
        factors += 5

    if factors > 0:
        final_compatibility = min(100, int(compatibility * 100 / factors))
    else:
        final_compatibility = 0

    if has_length:
        user_length = float(user_data['foot_length']) * 10
        shoe_length = shoe_size['length']
        if abs(user_length - shoe_length) <= 2:
            final_compatibility = min(100, final_compatibility + 5)

    return final_compatibility

def find_best_matches(user_email):
    user = get_user_by_email(user_email)
    if not user:
        return []

    shoes_db = load_shoes_database()
    recommendations = []

    for shoe in shoes_db['sneakers']:
        best_compatibility = 0
        best_size = None

        for size in shoe['sizes']:
            compatibility = calculate_compatibility({
                'foot_length': user.get('foot_length'),
                'foot_width': user.get('foot_width'),
                'arch': user.get('arch'),
                'foot_type': user.get('foot_type')
            }, size)

            if compatibility > best_compatibility:
                best_compatibility = compatibility
                best_size = size

        if best_compatibility >= 30:
            recommendations.append({
                'model': shoe['model'],
                'compatibility': best_compatibility,
                'best_size': best_size,
                'all_sizes': shoe['sizes']
            })

    recommendations.sort(key=lambda x: x['compatibility'], reverse=True)
    return recommendations[:8]

app = Flask(__name__)
app.secret_key = 'your-secret-key-123456789'

USERS_FILE = 'users.txt'
AVATARS_DIR = os.path.join('static', 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

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


def find_best_matches(user_email):
    user = get_user_by_email(user_email)
    if not user:
        print(f"Пользователь с email {user_email} не найден")
        return []

    shoes_db = load_shoes_database()
    recommendations = []

    for shoe in shoes_db['sneakers']:
        best_compatibility = 0
        best_size = None

        for size in shoe['sizes']:
            compatibility = calculate_compatibility({
                'foot_length': user.get('foot_length'),
                'foot_width': user.get('foot_width'),
                'arch': user.get('arch'),
                'foot_type': user.get('foot_type')
            }, size)

            if compatibility > best_compatibility:
                best_compatibility = compatibility
                best_size = size

        print(f"Модель: {shoe['model']}, Совместимость: {best_compatibility}")

        if best_compatibility > 30:
            recommendations.append({
                'model': shoe['model'],
                'compatibility': best_compatibility,
                'best_size': best_size,
                'all_sizes': shoe['sizes']
            })

    recommendations.sort(key=lambda x: x['compatibility'], reverse=True)
    return recommendations[:6]

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
    users.append([
        user_data.get('username', ''),
        user_data.get('email', ''),
        user_data.get('password', ''),
        user_data.get('registration_date', ''),
        user_data.get('registration_type', 'form'),
        '', '', '', '', '',
        '',
        ''
    ])
    save_users(users)
    return True


def update_user_measurements(email, data):
    users = load_users()
    changed = False
    for u in users:
        if u[1] == email:
            u[5] = data.get('length', '').strip() or ''
            u[6] = data.get('width', '').strip() or ''
            u[7] = data.get('arch', '').strip() or ''
            u[8] = ''
            u[9] = data.get('foot_type', '').strip() or ''
            changed = True
    if changed:
        save_users(users)


def update_user_profile(email, about=None, avatar_path=None):
    users = load_users()
    for u in users:
        if u[1] == email:
            old_avatar = u[10]
            if avatar_path:
                if old_avatar:
                    old_path = os.path.join(old_avatar.replace('/', os.sep))
                    if os.path.exists(old_path) and os.path.commonpath([os.path.abspath(old_path), os.path.abspath(AVATARS_DIR)]) == os.path.abspath(AVATARS_DIR):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                u[10] = avatar_path
            if about is not None:
                u[11] = about
    save_users(users)


def setup():
    ensure_storage()

setup()

@app.route('/shoe/<model_name>')
def shoe_detail(model_name):
    if not session.get('user_logged_in'):
        return redirect('/loggin')

    shoes_db = load_shoes_database()
    user = get_user_by_email(session.get('user_email'))

    shoe_data = None
    for shoe in shoes_db['sneakers']:
        if shoe['model'] == model_name:
            shoe_data = shoe
            break

    if not shoe_data:
        return "Модель не найдена", 404

    size_compatibilities = []
    for size in shoe_data['sizes']:
        compatibility = calculate_compatibility({
            'foot_length': user['foot_length'],
            'foot_width': user['foot_width'],
            'arch': user['arch'],
            'foot_type': user['foot_type']
        }, size)

        size_compatibilities.append({
            'size_data': size,
            'compatibility': compatibility
        })

    size_compatibilities.sort(key=lambda x: x['compatibility'], reverse=True)

    return render_template('shoe_detail.html',
                           shoe=shoe_data,
                           sizes=size_compatibilities,
                           user=user)


@app.route('/get_recommendations')
def get_recommendations():
    if not session.get('user_logged_in'):
        return jsonify({'error': 'Not logged in'})

    recommendations = find_best_matches(session.get('user_email'))
    return jsonify(recommendations)

@app.route('/')
def first():
    return render_template('first_page.html')


@app.route('/loggin')
def index():
    if session.get('user_logged_in'):
        return redirect('/')
    return render_template('register.html')


@app.route('/quick_login')
def quick_login():
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
    return redirect('/')


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

    return jsonify({'success': True, 'message': 'Регистрация успешна', 'redirect': '/'})


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

    return jsonify({'success': True, 'message': 'Вход успешен', 'redirect': '/'})


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
    if not session.get('user_logged_in'):
        return redirect('/loggin')
    email = session.get('user_email')
    about = request.form.get('about', '').strip()

    file = request.files.get('avatar')
    avatar_web_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            return "Неподдерживаемый формат изображения", 400

        ensure_storage()
        unique = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_name = f"{session.get('user_email').split('@')[0]}_{unique}.{ext}"
        save_path = os.path.join(AVATARS_DIR, new_name)
        file.save(save_path)
        avatar_web_path = os.path.join('static', 'avatars', new_name).replace('\\', '/')

    update_user_profile(email, about=about if about != '' else '', avatar_path=avatar_web_path)
    return redirect('/profile')

@app.route('/nickname_update', methods=['POST'])
def nickname_update():
    if not session.get('user_logged_in'):
        return redirect('/loggin')

    new_name = request.form.get('new_nickname', '').strip()
    email = session.get('user_email')

    if len(new_name) < 3:
        return "Имя слишком короткое"

    users = load_users()
    for u in users:
        if u[0] == new_name:
            return "Такой ник уже существует"

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

    user = get_user_by_email(session.get('user_email'))
    user_measurements = {
        'foot_length': user.get('foot_length', ''),
        'foot_width': user.get('foot_width', ''),
        'oblique_circumference': user.get('oblique_circumference', ''),  # Изменено здесь
        'foot_type': user.get('foot_type', '')
    }

    if request.method == 'POST':
        length = request.form.get('length', '').strip()
        width = request.form.get('width', '').strip()
        oblique_circumference = request.form.get('oblique_circumference', '').strip()  # Изменено здесь
        foot_type = request.form.get('foot_type', '').strip()

        errors = []

        # ... существующая валидация длины и ширины ...

        try:
            oblique_float = float(oblique_circumference)
            if oblique_float < 20 or oblique_float > 50:
                errors.append("Косой обхват должен быть от 20 до 50 см")
        except (ValueError, TypeError):
            errors.append("Некорректное значение косого обхвата")

        if not foot_type:
            errors.append("Выберите тип стопы")

        if errors:
            return render_template('measure.html',
                                   user_measurements=user_measurements,
                                   errors=errors)

        update_user_measurements(session.get('user_email'), {
            'length': length,
            'width': width,
            'oblique_circumference': oblique_circumference,  # Изменено здесь
            'foot_type': foot_type
        })
        return redirect('/profile')

    return render_template('measure.html',
                           user_measurements=user_measurements, errors=[])

@app.route('/users')
def view_users():
    if not os.path.exists(USERS_FILE):
        return "Пользователей пока нет"

    users = load_users()
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

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("how.html")

@app.route("/fit")
def fit():
    return render_template("fit.html")

@app.route('/get_random_shoe')
def get_random_shoe():
    try:
        shoes_db = load_shoes_database()
        if not shoes_db.get('sneakers'):
            return jsonify({'error': 'No shoes available'})

        # Выбираем случайную модель обуви
        random_shoe = random.choice(shoes_db['sneakers'])

        return jsonify({
            'model': random_shoe['model'],
            'sizes_available': len(random_shoe['sizes'])
        })

    except Exception as e:
        print(f"Error getting random shoe: {e}")
        return jsonify({'error': 'Failed to load shoe data'})


if __name__ == '__main__':
    ensure_storage()
    app.run(debug=True, host='0.0.0.0', port=5000)
