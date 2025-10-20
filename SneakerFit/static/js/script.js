document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        // Убираем активный класс у всех кнопок и контента
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Добавляем активный класс текущей кнопке и контенту
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab') + '-tab';
        document.getElementById(tabId).classList.add('active');
    });
});

// Обработка формы регистрации
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const btn = document.getElementById('registerBtn');
    const btnText = document.getElementById('registerBtnText');
    const spinner = document.getElementById('registerSpinner');
    const messageEl = document.getElementById('message');

    clearErrors('register');
    messageEl.style.display = 'none';

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;

    try {
        const formData = new FormData(this);
        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            if (result.redirect) {
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 1500);
            }
        } else {
            showMessage(result.message, 'error');
        }

    } catch (error) {
        showMessage('Ошибка сети. Проверьте подключение.', 'error');
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
});

// Обработка формы входа
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const btn = document.getElementById('loginBtn');
    const btnText = document.getElementById('loginBtnText');
    const spinner = document.getElementById('loginSpinner');
    const messageEl = document.getElementById('message');

    clearErrors('login');
    messageEl.style.display = 'none';

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;

    try {
        const formData = new FormData(this);
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            if (result.redirect) {
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 1500);
            }
        } else {
            showMessage(result.message, 'error');
        }

    } catch (error) {
        showMessage('Ошибка сети. Проверьте подключение.', 'error');
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
});

function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.innerHTML = `<div class="${type}">${text}</div>`;
    messageEl.style.display = 'block';
}

function clearErrors(formType) {
    const errors = document.querySelectorAll(`#${formType}-tab .error`);
    errors.forEach(error => error.textContent = '');
}

// Валидация в реальном времени для регистрации
document.getElementById('reg-username').addEventListener('blur', function() {
    if (this.value.length < 3 && this.value.length > 0) {
        document.getElementById('reg-usernameError').textContent = 'Минимум 3 символа';
    }
});

document.getElementById('reg-password').addEventListener('blur', function() {
    if (this.value.length < 6 && this.value.length > 0) {
        document.getElementById('reg-passwordError').textContent = 'Минимум 6 символов';
    }
});
