from flask import Flask, render_template, request, jsonify, redirect, session
import datetime
import os
import re
from werkzeug.utils import secure_filename
import random
import json
import string
from flask_mail import Mail, Message
from dotenv import load_dotenv
from functools import wraps
from database import setup_db, get_connection
from user_service import (
    user_exists, save_user_with_verification, get_user_by_email,
    update_user_measurements, update_user_profile,
    update_user_nickname, get_all_users, verify_user_email, is_email_verified
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-123456789')

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

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

pending_registrations = {}
pending_password_resets = {}

def send_verification_code(email, username, msg_type="verification"):
    """Отправляет код подтверждения на email"""
    try:
        code = ''.join(random.choices(string.digits, k=5))

        if msg_type == "verification":
            pending_registrations[email] = {
                'code': code,
                'username': username,
                'timestamp': datetime.datetime.now(),
                'verified': False,
                'attempts': 0
            }
            subject = 'Подтверждение email - SneakerFit'
            body = f'''Приветствуем, {username}!

            Ваш код подтверждения: {code}
            
            Введите этот код на сайте для завершения регистрации.
            
            Код действителен в течение 15 минут.
            
            С уважением,
            Команда SneakerFit'''
        elif msg_type == "password_reset":
            pending_password_resets[email] = {
                'code': code,
                'timestamp': datetime.datetime.now(),
                'attempts': 0,
                'used': False
            }
            subject = 'Сброс пароля - SneakerFit'
            body = f'''Приветствуем, {username}!

            Ваш код для сброса пароля: {code}
            
            Введите этот код на сайте для создания нового пароля.
            
            Код действителен в течение 15 минут.
            
            С уважением,
            Команда SneakerFit'''

        msg = Message(
            subject=subject,
            recipients=[email],
            body=body
        )
        mail.send(msg)
        print(f"Код {code} отправлен на {email}")
        return True

    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

def update_user_password(email, new_password):
    """Обновляет пароль пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET password = ? WHERE email = ?',
            (new_password, email)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка обновления пароля: {e}")
        return False

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
            factors += 29
        except ValueError:
            pass

    if has_oblique:
        try:
            user_oblique = float(user_data['oblique_circumference']) * 10
            shoe_oblique = shoe_size['obliqueCircumference']
            user_oblique += 10 if is_sport == 1 else 15
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


# ------------------ Декораторы для проверки авторизации ------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_logged_in'):
            return redirect('/login_page')
        return f(*args, **kwargs)

    return decorated_function


def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_logged_in'):
            return redirect('/login_page')

        user_email = session.get('user_email')
        if not user_email or not is_email_verified(user_email):
            session['redirect_after_verification'] = request.url
            return redirect('/verify_email_page')

        return f(*args, **kwargs)

    return decorated_function


# ------------------ Роуты(ссылки) ------------------

@app.route('/')
def first():
    return render_template('first_page.html')


@app.route('/shoe/<model_name>')
@email_verified_required
def shoe_detail(model_name):
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
                           shoe=shoe, sizes=sizes_compatibility, user=user)


@app.route('/get_shoe_type')
def get_shoe_type():
    model_name = request.args.get('model', '')
    shoes_db = load_shoes_database()

    for shoe in shoes_db['sneakers']:
        if shoe['model'] == model_name:
            shoe_type = 'sport' if shoe.get('sport', 1) == 1 else 'casual'
            return jsonify({'shoeType': shoe_type})

    return jsonify({'shoeType': 'sport'})


# ------------------ Регистрация и подтверждение email ------------------

@app.route('/register_page')
def register_page():
    if session.get('user_logged_in'):
        return redirect('/')
    return render_template('register.html')


@app.route('/verify_email_page')
def verify_email_page():
    if not session.get('user_logged_in') and 'pending_email' not in session:
        return redirect('/register_page')
    return render_template('verify_email.html')


@app.route('/login_page')
def login_page():
    if session.get('user_logged_in'):
        return redirect('/')
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        print(f"=== DEBUG LOGIN ===")
        print(f"Email: '{email}'")
        print(f"Password entered: '{password}'")
        print(f"Password length: {len(password)}")

        if not email or not password:
            return jsonify({'success': False, 'message': 'Введите email и пароль'})

        user = get_user_by_email(email)

        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        print(f"User found: {bool(user)}")
        if user:
            print(f"Stored password: '{user['password']}'")
            print(f"Stored password length: {len(user['password'])}")
            print(f"Passwords match: {user['password'] == password}")

        if user['password'] != password:
            return jsonify({'success': False, 'message': 'Неверный пароль'})

        if not user.get('email_verified'):
            session['pending_email'] = email
            session['pending_username'] = user['username']
            session['pending_password'] = password

            send_verification_code(email, user['username'])

            return jsonify({
                'success': True,
                'message': 'Email не подтвержден. Код отправлен на почту.',
                'redirect': '/verify_email_page'
            })

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


@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        print(f"Registration attempt: {username}, {email}")

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'Все поля обязательны'})
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Имя слишком короткое'})
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Неверный email'})
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})
        if password == username:
            return jsonify({'success': False, 'message': 'Пароль не может совпадать с логином'})
        if password.isdigit():
            return jsonify({'success': False, 'message': 'Пароль не может состоять только из цифр'})
        if password.isalpha():
            return jsonify({'success': False, 'message': 'Пароль не может состоять только из букв'})
        if user_exists(email):
            return jsonify({'success': False, 'message': 'Пользователь уже существует'})

        if not send_verification_code(email, username):
            return jsonify({'success': False, 'message': 'Ошибка отправки кода подтверждения'})

        session['pending_email'] = email
        session['pending_username'] = username
        session['pending_password'] = password

        return jsonify({
            'success': True,
            'message': 'Код подтверждения отправлен на email',
            'redirect': '/verify_email_page'
        })

    except Exception as e:
        print(f"Error in register: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/verify_email', methods=['POST'])
def verify_email():
    try:
        code = request.form.get('code', '').strip()

        if not code:
            return jsonify({'success': False, 'message': 'Введите код подтверждения'})

        email = session.get('pending_email')
        username = session.get('pending_username')
        password = session.get('pending_password')

        if not email or not username:
            return jsonify({'success': False, 'message': 'Сессия истекла. Начните регистрацию заново.'})

        if email not in pending_registrations:
            return jsonify({'success': False, 'message': 'Код не найден или истек'})

        verification_data = pending_registrations[email]

        time_diff = datetime.datetime.now() - verification_data['timestamp']
        if time_diff.total_seconds() > 900:
            del pending_registrations[email]
            return jsonify({'success': False, 'message': 'Код истек. Запросите новый.'})

        if verification_data['code'] != code:
            verification_data.setdefault('attempts', 0)
            verification_data['attempts'] += 1

            if verification_data['attempts'] >= 3:
                del pending_registrations[email]
                return jsonify({'success': False, 'message': 'Слишком много попыток. Запросите новый код.'})

            return jsonify({'success': False, 'message': 'Неверный код'})

        success = save_user_with_verification({
            'username': username,
            'email': email,
            'password': password,
            'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'registration_type': 'form'
        })

        if not success:
            return jsonify({'success': False, 'message': 'Ошибка при сохранении пользователя'})

        verify_user_email(email)

        session['user_logged_in'] = True
        session['user_email'] = email
        session['user_name'] = username

        del pending_registrations[email]
        session.pop('pending_email', None)
        session.pop('pending_username', None)
        session.pop('pending_password', None)

        redirect_url = session.pop('redirect_after_verification', '/')

        return jsonify({
            'success': True,
            'message': 'Email успешно подтвержден!',
            'redirect': redirect_url
        })

    except Exception as e:
        print(f"Error in verify_email: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/resend_verification_code', methods=['POST'])
def resend_verification_code():
    """Повторная отправка кода подтверждения"""
    try:
        email = session.get('pending_email')

        if not email:
            return jsonify({'success': False, 'message': 'Сессия истекла'})
        if email in pending_registrations:
            username = session.get('pending_username', 'Пользователь')
            last_send = pending_registrations[email].get('last_resend')
            if last_send:
                time_diff = datetime.datetime.now() - last_send
                if time_diff.total_seconds() < 60:
                    return jsonify({'success': False, 'message': 'Подождите 60 секунд перед повторной отправкой'})

            send_verification_code(email, username)
            pending_registrations[email]['last_resend'] = datetime.datetime.now()

            return jsonify({'success': True, 'message': 'Код отправлен повторно'})
        else:
            username = session.get('pending_username', 'Пользователь')
            send_verification_code(email, username)
            return jsonify({'success': True, 'message': 'Код отправлен'})

    except Exception as e:
        print(f"Error in resend_verification_code: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ------------------ Остальные маршруты ------------------

@app.route('/change_password_page')
def change_password_page():
    """Страница изменения пароля из профиля"""
    if not session.get('user_logged_in') and not session.get('reset_email'):
        return redirect('/login_page')

    return render_template('change_password.html')

@app.route('/forgot_password_page')
def forgot_password_page():
    """Страница ввода email для сброса пароля"""
    return render_template('forgot_password.html')

@app.route('/reset_password_page')
def reset_password_page():
    """Страница ввода кода подтверждения"""
    if 'reset_email' not in session:
        return redirect('/forgot_password_page')
    return render_template('reset_password.html')


@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    """Обработка запроса на сброс пароля"""
    try:
        email = request.form.get('email', '').strip()

        if not email:
            return jsonify({'success': False, 'message': 'Введите email'})
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Неверный формат email'})
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь с таким email не найден'})

        if email in pending_password_resets:
            time_diff = datetime.datetime.now() - pending_password_resets[email]['timestamp']
            if time_diff.total_seconds() < 60:
                return jsonify({
                    'success': False,
                    'message': f'Подождите {60 - int(time_diff.total_seconds())} секунд перед повторной отправкой'
                })
        if not send_verification_code(email, user['username'], "password_reset"):
            return jsonify({'success': False, 'message': 'Ошибка отправки кода'})

        session['reset_email'] = email
        session['reset_username'] = user['username']

        return jsonify({
            'success': True,
            'message': 'Код отправлен на ваш email',
            'redirect': '/reset_password_page'
        })
    except Exception as e:
        print(f"Ошибка в forgot_password: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/verify_reset_code', methods=['POST'])
def verify_reset_code():
    """Проверка кода сброса пароля"""
    try:
        code = request.form.get('code', '').strip()

        print(f"=== DEBUG verify_reset_code ===")
        print(f"Code: {code}")
        print(f"Session keys: {list(session.keys())}")
        print(f"Reset email in session: {session.get('reset_email')}")
        print(f"Reset username in session: {session.get('reset_username')}")

        if not code:
            return jsonify({'success': False, 'message': 'Введите код подтверждения'})

        email = session.get('reset_email')

        if not email:
            return jsonify({'success': False, 'message': 'Сессия истекла'})

        if email not in pending_password_resets:
            return jsonify({'success': False, 'message': 'Код не найден или истек'})

        reset_data = pending_password_resets[email]

        time_diff = datetime.datetime.now() - reset_data['timestamp']
        if time_diff.total_seconds() > 900:
            del pending_password_resets[email]
            return jsonify({'success': False, 'message': 'Код истек. Запросите новый.'})

        if reset_data.get('attempts', 0) >= 4:
            del pending_password_resets[email]
            return jsonify({'success': False, 'message': 'Слишком много попыток. Запросите новый код.'})

        if reset_data['code'] != code:
            reset_data['attempts'] = reset_data.get('attempts', 0) + 1
            return jsonify({'success': False, 'message': 'Неверный код'})

        reset_data['used'] = True

        print(f"=== DEBUG Code verified successfully ===")
        print(f"Redirecting to change_password_page")

        return jsonify({
            'success': True,
            'message': 'Код подтвержден',
            'redirect': '/change_password_page'
        })

    except Exception as e:
        print(f"Ошибка в verify_reset_code: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/change_password', methods=['POST'])
def change_password():
    """Изменение пароля (из профиля или после сброса)"""
    try:
        email = session.get('user_email') or session.get('reset_email')
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        print(f"=== DEBUG change_password ===")
        print(f"Email from session: {email}")
        print(f"User email: {session.get('user_email')}")
        print(f"Reset email: {session.get('reset_email')}")
        if not email:
            return jsonify({'success': False, 'message': 'Сессия истекла'})
        if not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'Введите новый пароль и подтверждение'})
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Пароли не совпадают'})
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})
        if new_password.isdigit():
            return jsonify({'success': False, 'message': 'Пароль не может состоять только из цифр'})
        if new_password.isalpha():
            return jsonify({'success': False, 'message': 'Пароль не может состоять только из букв'})

        user = get_user_by_email(email)
        if user and new_password == user['username']:
            return jsonify({'success': False, 'message': 'Пароль не может совпадать с логином'})

        if not update_user_password(email, new_password):
            return jsonify({'success': False, 'message': 'Ошибка обновления пароля'})

        if 'reset_email' in session:
            session.pop('reset_email', None)
            session.pop('reset_username', None)
            if email in pending_password_resets:
                del pending_password_resets[email]

        if 'user_email' not in session:
            session['user_logged_in'] = True
            session['user_email'] = email
            session['user_name'] = user['username']

        return jsonify({
            'success': True,
            'message': 'Пароль успешно изменен',
            'redirect': '/profile'
        })
    except Exception as e:
        print(f"Ошибка в change_password: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})


@app.route('/resend_reset_code', methods=['POST'])
def resend_reset_code():
    """Повторная отправка кода сброса пароля"""
    try:
        email = session.get('reset_email')

        if not email:
            return jsonify({'success': False, 'message': 'Сессия истекла'})

        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        if email in pending_password_resets:
            last_send = pending_password_resets[email].get('last_resend')
            if last_send:
                time_diff = datetime.datetime.now() - last_send
                if time_diff.total_seconds() < 60:
                    return jsonify({
                        'success': False,
                        'message': 'Подождите 60 секунд перед повторной отправкой'
                    })

        send_verification_code(email, user['username'], "password_reset")
        pending_password_resets[email]['last_resend'] = datetime.datetime.now()

        return jsonify({'success': True, 'message': 'Код отправлен повторно'})

    except Exception as e:
        print(f"Ошибка в resend_reset_code: {e}")
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'})

@app.route('/profile')
@email_verified_required
def profile():
    user = get_user_by_email(session.get('user_email'))
    return render_template('profile.html', user=user)


@app.route('/profile_update', methods=['POST'])
@email_verified_required
def profile_update():
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
@email_verified_required
def nickname_update():
    new_name = request.form.get('new_nickname', '').strip()
    if len(new_name) < 3:
        return "Имя слишком короткое"
    if new_name in [u['username'] for u in get_all_users()]:
        return "Такой ник уже существует"
    update_user_nickname(session.get('user_email'), new_name)
    session['user_name'] = new_name
    return redirect('/profile')


@app.route('/measure', methods=['GET', 'POST'])
@email_verified_required
def measure():
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
@login_required
def get_recommendations():
    if not is_email_verified(session.get('user_email')):
        return jsonify({'error': 'Email not verified', 'redirect': '/verify_email_page'})

    recommendations = find_best_matches(session.get('user_email'))
    return jsonify(recommendations)


@app.route('/users')
def view_users():
    users = get_all_users()
    html = "<h1>Пользователи</h1><table border='1'><tr><th>Имя</th><th>Email</th><th>Подтвержден</th></tr>"
    for u in users:
        verified = "Да" if u.get('email_verified') else "Нет"
        html += f"<tr><td>{u['username']}</td><td>{u['email']}</td><td>{verified}</td></tr>"
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
@email_verified_required
def fit():
    return render_template("fit.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
