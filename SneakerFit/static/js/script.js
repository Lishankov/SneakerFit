document.addEventListener('DOMContentLoaded', function() {
    initializeForms();
    initializeAvatarPreview();
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

function initializeAvatarPreview() {
    const avatarInput = document.getElementById('avatarInput');
    if (avatarInput) {
        avatarInput.addEventListener('change', function(evt) {
            const file = evt.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.getElementById('avatarPreview');
                if (img) img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    const btnText = document.getElementById('registerBtnText');
    const spinner = document.getElementById('registerSpinner');
    const messageEl = document.getElementById('message');

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;
    messageEl.style.display = 'none';

    try {
        const formData = new FormData(this);
        const r = await fetch('/register', { method:'POST', body: formData });
        const result = await r.json();
        if (result.success) {
            messageEl.innerHTML = `<div class="success">${result.message}</div>`;
            messageEl.style.display = 'block';
            setTimeout(()=> { window.location.href = result.redirect; }, 1000);
        } else {
            messageEl.innerHTML = `<div class="error">${result.message}</div>`;
            messageEl.style.display = 'block';
        }
    } catch (err) {
        messageEl.innerHTML = `<div class="error">Ошибка сети</div>`;
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

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    btn.disabled = true;
    messageEl.style.display = 'none';

    try {
        const formData = new FormData(this);
        const r = await fetch('/login', { method:'POST', body: formData });
        const result = await r.json();
        if (result.success) {
            messageEl.innerHTML = `<div class="success">${result.message || 'Вход'}</div>`;
            messageEl.style.display = 'block';
            setTimeout(()=> window.location.href = result.redirect || '/welcome', 700);
        } else {
            messageEl.innerHTML = `<div class="error">${result.message}</div>`;
            messageEl.style.display = 'block';
        }
    } catch (err) {
        messageEl.innerHTML = `<div class="error">Ошибка сети</div>`;
        messageEl.style.display = 'block';
    } finally {
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}