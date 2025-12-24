document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('changePasswordForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('spinner');
    const messageEl = document.getElementById('message');

    window.togglePassword = function(inputId) {
        const input = document.getElementById(inputId);
        const button = input.parentElement.querySelector('.toggle-password');

        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '👁';
            button.setAttribute('aria-label', 'Скрыть пароль');
        } else {
            input.type = 'password';
            button.textContent = '👁';
            button.setAttribute('aria-label', 'Показать пароль');
        }
    };

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const newPassword = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        if (newPassword.length < 6) {
            showMessage('Пароль должен быть не менее 6 символов', 'error');
            return;
        }
        if (newPassword !== confirmPassword) {
            showMessage('Пароли не совпадают', 'error');
            return;
        }
        if (newPassword.isdigit()) {
            showMessage('Пароль не может состоять только из цифр', 'error');
            return;
        }
        if (newPassword.isalpha()) {
            showMessage('Пароль не может состоять только из букв', 'error');
            return;
        }
        const simplePasswords = ['password', '123456', 'qwerty', 'пароль', '000000'];
        if (simplePasswords.includes(newPassword.toLowerCase())) {
            showMessage('Пароль слишком простой. Выберите более сложный пароль.', 'error');
            return;
        }

        btnText.style.display = 'none';
        spinner.style.display = 'inline-block';
        submitBtn.disabled = true;
        messageEl.style.display = 'none';

        try {
            const formData = new FormData(this);

            const response = await fetch('/change_password', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                showMessage(result.message, 'success');
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 1500);
            } else {
                showMessage(result.message, 'error');
            }
        } catch (error) {
            showMessage('Ошибка сети: ' + error.message, 'error');
        } finally {
            btnText.style.display = 'inline-block';
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    function showMessage(text, type) {
        messageEl.innerHTML = `<div class="${type}">${text}</div>`;
        messageEl.style.display = 'block';

        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }

    document.querySelectorAll('.password-wrapper input').forEach(input => {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const form = document.getElementById('changePasswordForm');
                const submitBtn = document.getElementById('submitBtn');

                if (form && submitBtn) {
                    submitBtn.click();
                }
            }
        });
    });
});