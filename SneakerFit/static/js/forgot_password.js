document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('forgotPasswordForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('spinner');
    const messageEl = document.getElementById('message');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        btnText.style.display = 'none';
        spinner.style.display = 'inline-block';
        submitBtn.disabled = true;
        messageEl.style.display = 'none';

        try {
            const formData = new FormData(this);

            const response = await fetch('/forgot_password', {
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
    }
});