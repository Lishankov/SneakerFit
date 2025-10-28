from flask import Flask, render_template, request, jsonify, redirect, session
import datetime
import os
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-123456789'

USERS_FILE = 'users.txt'

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def user_exists(email):
    if not os.path.exists(USERS_FILE):
        return False

    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if f"| {email} |" in line:
                    return True
    except:
        pass
    return False

def save_user(user_data):
    try:
        data_string = f"{user_data['username']} | {user_data['email']} | {user_data['password']} | {user_data['registration_date']} | {user_data.get('registration_type', 'form')}\n"

        with open(USERS_FILE, 'a', encoding='utf-8') as f:
            f.write(data_string)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def get_user_by_email(email):
    if not os.path.exists(USERS_FILE):
        return None

    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' | ')
                if len(parts) >= 4 and parts[1] == email:
                    return {
                        'username': parts[0],
                        'email': parts[1],
                        'password': parts[2],
                        'registration_date': parts[3],
                        'registration_type': parts[4] if len(parts) > 4 else 'form'
                    }
    except:
        pass
    return None

@app.route('/')
def first():
    return render_template('first_page.html')

@app.route('/loggin')
def index():
    if session.get('user_logged_in'):
        return redirect('/welcome')
    return render_template('register.html')


@app.route('/profile')
def profile():
    if not session.get('user_logged_in'):
        return redirect('/loggin')
    return redirect('/welcome')


@app.route('/measure')
def measure():
    if not session.get('user_logged_in'):
        return redirect('/loggin')
    return render_template('measure.html')


@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'Все поля обязательны'})

        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Минимум 3 символа'})

        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Введите корректный email'})

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Пароль слишком короткий'})

        if user_exists(email):
            return jsonify({'success': False, 'message': 'Пользователь уже существует'})

        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if save_user(user_data):
            session['user_logged_in'] = True
            session['user_email'] = email
            session['user_name'] = username

            return jsonify({'success': True, 'message': 'Готово!', 'redirect': '/welcome'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка сохранения'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = get_user_by_email(email)

        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        if user['password'] != password:
            return jsonify({'success': False, 'message': 'Неверный пароль'})

        session['user_logged_in'] = True
        session['user_email'] = email
        session['user_name'] = user['username']

        return jsonify({'success': True, 'redirect': '/welcome'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/welcome')
def welcome():
    if not session.get('user_logged_in'):
        return redirect('/')
    return render_template('welcome.html', username=session['user_name'], email=session['user_email'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/users')
def view_users():
    """Страница для просмотра зарегистрированных пользователей"""
    if not os.path.exists(USERS_FILE):
        return "Пользователей пока нет"

    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = f.readlines()

        users_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Зарегистрированные пользователи</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
                .demo-user { background-color: #f0fff0; }
            </style>
        </head>
        <body>
            <h1>Зарегистрированные пользователи</h1>
            <table>
                <tr>
                    <th>Имя пользователя</th>
                    <th>Email</th>
                    <th>Пароль</th>
                    <th>Дата регистрации</th>
                    <th>Тип</th>
                </tr>
        """

        for user in users:
            parts = user.strip().split(' | ')
            if len(parts) >= 4:
                user_class = 'demo-user' if len(parts) > 4 and parts[4] == 'demo' else ''
                reg_type = 'Демо' if len(parts) > 4 and parts[4] == 'demo' else 'Форма'
                users_html += f"""
                <tr class="{user_class}">
                    <td>{parts[0]}</td>
                    <td>{parts[1]}</td>
                    <td><code>{parts[2]}</code></td>
                    <td>{parts[3]}</td>
                    <td>{reg_type}</td>
                </tr>
                """

        users_html += """
            </table>
            <br>
            <a href="/">← Вернуться на главную</a>
        </body>
        </html>
        """

        return users_html
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

if __name__ == '__main__':
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    app.run(debug=True, host='0.0.0.0', port=5000)
