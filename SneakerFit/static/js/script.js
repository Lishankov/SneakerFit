document.addEventListener('DOMContentLoaded', function() {
    initializeForms();
});

function initializeForms() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    const btnText = document.getElementById('registerBtnText');
    const spinner = document.getElementById('registerSpinner');
    const messageEl = document.getElementById('message');

    if (!btn || !btnText || !spinner || !messageEl) {
        console.error('Register elements not found');
        return;
    }

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;
    messageEl.style.display = 'none';

    try {
        const formData = new FormData(this);
        
        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            messageEl.innerHTML = `<div class="success">${result.message}</div>`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                window.location.href = result.redirect || '/';
            }, 1000);
        } else {
            messageEl.innerHTML = `<div class="error">${result.message}</div>`;
            messageEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Register error:', error);
        messageEl.innerHTML = `<div class="error">Ошибка сети: ${error.message}</div>`;
        messageEl.style.display = 'block';
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    const btnText = document.getElementById('loginBtnText');
    const spinner = document.getElementById('loginSpinner');
    const messageEl = document.getElementById('message');

    if (!btn || !btnText || !spinner || !messageEl) {
        console.error('Login elements not found');
        return;
    }

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;
    messageEl.style.display = 'none';

    try {
        const formData = new FormData(this);
        
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            messageEl.innerHTML = `<div class="success">${result.message || 'Вход успешен'}</div>`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                window.location.href = result.redirect || '/';
            }, 700);
        } else {
            messageEl.innerHTML = `<div class="error">${result.message}</div>`;
            messageEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        messageEl.innerHTML = `<div class="error">Ошибка сети: ${error.message}</div>`;
        messageEl.style.display = 'block';
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}

const style = document.createElement('style');
style.textContent = `
    .success {
        color: #4CAF50;
        background: #E8F5E8;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
    }
    .error {
        color: #f44336;
        background: #FFEBEE;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
    }
    .message {
        margin-top: 15px;
    }
`;
document.head.appendChild(style);
// Дополнительные функции для работы с email подтверждением
function handleRegistrationResponse(result, messageEl) {
    if (result.success) {
        messageEl.innerHTML = `<div class="success">${result.message}</div>`;
        messageEl.style.display = 'block';
        setTimeout(() => {
            window.location.href = result.redirect || '/';
        }, 1500);
    } else {
        messageEl.innerHTML = `<div class="error">${result.message}</div>`;
        messageEl.style.display = 'block';
    }
}

// Обновите функцию handleRegister в script.js
async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    const btnText = document.getElementById('registerBtnText');
    const spinner = document.getElementById('registerSpinner');
    const messageEl = document.getElementById('message');

    if (!btn || !btnText || !spinner || !messageEl) {
        console.error('Register elements not found');
        return;
    }

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;
    messageEl.style.display = 'none';

    try {
        const formData = new FormData(this);

        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        handleRegistrationResponse(result, messageEl);

    } catch (error) {
        console.error('Register error:', error);
        messageEl.innerHTML = `<div class="error">Ошибка сети: ${error.message}</div>`;
        messageEl.style.display = 'block';
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}