from flask import Flask, render_template, request, jsonify, redirect, session
import datetime
import os
import re
from werkzeug.utils import secure_filename
import random
import json
from database import setup_db, get_connection
from user_service import (
    user_exists, save_user, get_user_by_email,
    update_user_measurements, update_user_profile,
    update_user_nickname, get_all_users
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-123456789'

AVATARS_DIR = os.path.join('static', 'avatars')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
USERS_DB = 'users.db'

# ------------------ Инициализация ------------------

def ensure_storage():
    if not os.path.exists(AVATARS_DIR):
        os.makedirs(AVATARS_DIR, exist_ok=True)

setup_db()
ensure_storage()

# ------------------ Вспомогательные функции ------------------

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def load_shoes_database():
    try:
        with open('base_of_shoes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"sneakers": []}

def calculate_compatibility(user_data, shoe_size, is_sport=1):
    compatibility = 0
    factors = 0

    has_length = user_data.get('foot_length') and str(user_data['foot_length']).strip()
    has_width = user_data.get('foot_width') and str(user_data['foot_width']).strip()
    has_oblique = user_data.get('oblique_circumference') and str(user_data['oblique_circumference']).strip()
    has_foot_type = user_data.get('foot_type') and user_data['foot_type'].strip()

    if has_length:
        try:
            user_length = float(user_data['foot_length']) * 10
            shoe_length = shoe_size['length']
            user_length += 10 if is_sport == 1 else 15
            length_diff = abs(user_length - shoe_length)
            if length_diff <= 3: length_score = 45
            elif length_diff <= 7: length_score = 40
            elif length_diff <= 12: length_score = 35
            elif length_diff <= 17: length_score = 25
            elif length_diff <= 22: length_score = 15
            else: length_score = 5
            compatibility += length_score
            factors += 46
        except ValueError:
            pass

    if has_width:
        try:
            user_width = float(user_data['foot_width']) * 10
            estimated_midfoot = 2 * (user_width + 50) * 0.9
            user_width += 10 if is_sport == 1 else 15
            shoe_midfoot = shoe_size['midfootCircumference']
            width_diff = abs(estimated_midfoot - shoe_midfoot)
            if width_diff <= 15: width_score = 35
            elif width_diff <= 25: width_score = 30
            elif width_diff <= 35: width_score = 25
            elif width_diff <= 45: width_score = 18
            elif width_diff <= 55: width_score = 10
            else: width_score = 5
            compatibility += width_score
            factors += 29
        except ValueError:
            pass

    if has_oblique:
        try:
            user_oblique = float(user_data['oblique_circumference']) * 10
            shoe_oblique = shoe_size['obliqueCircumference']
            user_oblique += 10 if is_sport == 1 else 15
            oblique_diff = abs(user_oblique - shoe_oblique)
            if oblique_diff <= 10: oblique_score = 15
            elif oblique_diff <= 20: oblique_score = 12
            elif oblique_diff <= 30: oblique_score = 8
            elif oblique_diff <= 40: oblique_score = 5
            else: oblique_score = 2
            compatibility += oblique_score
            factors += 17
        except ValueError:
            pass

    if has_foot_type:
        foot_type = user_data['foot_type']
        if foot_type == 'Плоскостопие':
            ankle_circ = shoe_size['ankleCircumference']
            midfoot_circ = shoe_size['midfootCircumference']
            foot_type_score = 5 if ankle_circ > 240 and midfoot_circ > 220 else 3 if ankle_circ > 230 and midfoot_circ > 210 else 1
        elif foot_type == 'Супинация':
            toe_circ = shoe_size['toeCircumference']
            foot_type_score = 5 if toe_circ > 240 else 3 if toe_circ > 220 else 1
        else:
            foot_type_score = 4
        compatibility += foot_type_score
        factors += 8

    final_compatibility = min(98, int(compatibility * 100 / factors)) if factors > 0 else 0

    if has_length:
        user_length = float(user_data['foot_length']) * 10
        shoe_length = shoe_size['length'] + (4 if is_sport == 1 else 6)
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
            }, size, is_sport=shoe.get('sport', 1))
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

# ------------------ Роуты(ссылки) ------------------
@app.route('/shoe/<model_name>')
def shoe_detail(model_name):
    if not session.get('user_logged_in'):
        return redirect('/login_page')

    shoes_db = load_shoes_database()
    shoe = None
    for s in shoes_db['sneakers']:
        if s['model'] == model_name:
            shoe = s
            break
    if not shoe:
        return "Модель не найдена", 404

    user = get_user_by_email(session.get('user_email'))
    if not user:
        return redirect('/login_page')

    sizes_compatibility = []
    for size in shoe['sizes']:
        compatibility = calculate_compatibility({
            'foot_length': user.get('foot_length'),
            'foot_width': user.get('foot_width'),
            'oblique_circumference': user.get('oblique_circumference'),
            'foot_type': user.get('foot_type')
        }, size, is_sport=shoe.get('sport', 1))

        sizes_compatibility.append({
            'size_data': size,
            'compatibility': compatibility
        })

    sizes_compatibility.sort(key=lambda x: x['compatibility'], reverse=True)

    return render_template('shoe_detail.html',
                           shoe=shoe,
                           sizes=sizes_compatibility,
                           user=user)

@app.route('/')
def first():
    return render_template('first_page.html')

@app.route('/get_shoe_type')
def get_shoe_type():
    model_name = request.args.get('model', '')
    shoes_db = load_shoes_database()

    for shoe in shoes_db['sneakers']:
        if shoe['model'] == model_name:
            shoe_type = 'sport' if shoe.get('sport', 1) == 1 else 'casual'
            return jsonify({'shoeType': shoe_type})

    return jsonify({'shoeType': 'sport'})

@app.route('/register_page')
def register_page():
    if session.get('user_logged_in'):
        return redirect('/')
    return render_template('register.html')

@app.route('/login_page')
def login_page():
    if session.get('user_logged_in'):
        return redirect('/')
    return render_template('login.html')

@app.route('/login')
def login_redirect():
    return redirect('/login_page')


@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        print(f"Registration attempt: {username}, {email}")  # Debug log

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'Все поля обязательны'})
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Имя слишком короткое'})
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Неверный email'})
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})

        # Проверяем существование пользователя
        if user_exists(email):
            return jsonify({'success': False, 'message': 'Пользователь уже существует'})

        # Сохраняем пользователя
        success = save_user({
            'username': username,
            'email': email,
            'password': password,
            'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'registration_type': 'form'
        })

        if not success:
            return jsonify({'success': False, 'message': 'Ошибка при сохранении пользователя'})

        # Устанавливаем сессию
        session['user_logged_in'] = True
        session['user_email'] = email
        session['user_name'] = username

        return jsonify({
            'success': True,
            'message': 'Регистрация успешна',
            'redirect': '/'
        })

    except Exception as e:
        print(f"Error in register: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        print(f"Login attempt: {email}")  # Debug log

        if not email or not password:
            return jsonify({'success': False, 'message': 'Введите email и пароль'})

        user = get_user_by_email(email)
        print(f"User found: {user}")  # Debug log

        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        # Сравниваем пароли
        if user['password'] != password:
            return jsonify({'success': False, 'message': 'Неверный пароль'})

        # Устанавливаем сессию
        session['user_logged_in'] = True
        session['user_email'] = email
        session['user_name'] = user['username']

        return jsonify({
            'success': True,
            'message': 'Вход успешен',
            'redirect': '/'
        })

    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})

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
    if len(new_name) < 3:
        return "Имя слишком короткое"
    if new_name in [u['username'] for u in get_all_users()]:
        return "Такой ник уже существует"
    update_user_nickname(session.get('user_email'), new_name)
    session['user_name'] = new_name
    return redirect('/profile')

@app.route('/measure', methods=['GET', 'POST'])
def measure():
    if not session.get('user_logged_in'):
        return redirect('/login_page')
    user = get_user_by_email(session.get('user_email'))
    if request.method == 'POST':
        length = request.form.get('length', '').strip()
        width = request.form.get('width', '').strip()
        oblique_circumference = request.form.get('oblique_circumference', '').strip()
        foot_type = request.form.get('foot_type', '').strip()
        errors = []
        try:
            oblique_float = float(oblique_circumference)
            if oblique_float < 20 or oblique_float > 50:
                errors.append("Косой обхват должен быть от 20 до 50 см")
        except:
            errors.append("Некорректное значение косого обхвата")
        if not foot_type:
            errors.append("Выберите тип стопы")
        if errors:
            return render_template('measure.html', user_measurements=user, errors=errors)
        update_user_measurements(session.get('user_email'), {
            'length': length,
            'width': width,
            'oblique_circumference': oblique_circumference,
            'foot_type': foot_type
        })
        return redirect('/profile')
    return render_template('measure.html', user_measurements=user, errors=[])

@app.route('/get_recommendations')
def get_recommendations():
    if not session.get('user_logged_in'):
        return jsonify({'error': 'Not logged in'})
    recommendations = find_best_matches(session.get('user_email'))
    return jsonify(recommendations)

@app.route('/users')
def view_users():
    users = get_all_users()
    html = "<h1>Пользователи</h1><table border='1'><tr><th>Имя</th><th>Email</th></tr>"
    for u in users:
        html += f"<tr><td>{u['username']}</td><td>{u['email']}</td></tr>"
    html += "</table>"
    return html

@app.route('/get_random_shoe')
def get_random_shoe():
    try:
        shoes_db = load_shoes_database()
        if not shoes_db.get('sneakers'):
            return jsonify({'error': 'No shoes available'})
        random_shoe = random.choice(shoes_db['sneakers'])
        return jsonify({
            'model': random_shoe['model'],
            'sizes_available': len(random_shoe['sizes'])
        })
    except Exception as e:
        print(f"Error getting random shoe: {e}")
        return jsonify({'error': 'Failed to load shoe data'})

# ------------------ Статические страницы ------------------

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("how.html")

@app.route("/fit")
def fit():
    return render_template("fit.html")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
