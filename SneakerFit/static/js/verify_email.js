document.addEventListener('DOMContentLoaded', function() {
    const isResetPassword = window.location.pathname.includes('reset_password') ||
                          document.title.includes('Сброс пароля') ||
                          document.title.includes('Подтверждение кода');

    const codeInputs = document.querySelectorAll('.code-input');
    const hiddenCodeInput = document.getElementById('verificationCode');
    const verifyForm = document.getElementById('verifyForm') || document.getElementById('verifyResetForm');
    const resendBtn = document.getElementById('resendBtn');
    const messageEl = document.getElementById('message');
    const timerElement = document.getElementById('timer');
    const resendTimerElement = document.getElementById('resendTimer');
    const resendCountdownElement = document.getElementById('resendCountdown');

    let timeLeft = 15 * 60;
    let timerInterval;

    let resendTimeLeft = 60;
    let resendTimerInterval;

    initCodeInputs();
    startTimer();
    setupEventListeners();

    function initCodeInputs() {
        codeInputs.forEach((input, index) => {
            input.addEventListener('input', function(e) {
                if (this.value && !/^\d$/.test(this.value)) {
                    this.value = '';
                    return;
                }

                updateHiddenCode();

                if (this.value && index < codeInputs.length - 1) {
                    codeInputs[index + 1].focus();
                }
            });

            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && !this.value && index > 0) {
                    codeInputs[index - 1].focus();
                }
                if (e.key === 'ArrowLeft' && index > 0) {
                    codeInputs[index - 1].focus();
                }
                if (e.key === 'ArrowRight' && index < codeInputs.length - 1) {
                    codeInputs[index + 1].focus();
                }
            });

            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const pasteData = e.clipboardData.getData('text').trim();

                if (pasteData.length === 5 && /^\d{5}$/.test(pasteData)) {
                    const digits = pasteData.split('');
                    codeInputs.forEach((input, i) => {
                        if (i < 5) {
                            input.value = digits[i];
                        }
                    });
                    updateHiddenCode();
                    codeInputs[4].focus();
                }
            });

            input.addEventListener('focus', function() {
                this.select();
            });
        });
    }

    function updateHiddenCode() {
        const codeArray = [];
        codeInputs.forEach(input => {
            codeArray.push(input.value);
        });
        hiddenCodeInput.value = codeArray.join('');
    }

    function startTimer() {
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerElement.textContent = `Код действителен: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        if (timeLeft <= 60) {
            timerElement.classList.add('expired');
        }

        if (timeLeft <= 0) {
            timerElement.textContent = 'Код истек';
            clearInterval(timerInterval);
            return;
        }
        timeLeft--;
    }

    function startResendTimer() {
        resendTimeLeft = 60;
        resendTimerElement.style.display = 'block';
        updateResendTimer();
        resendTimerInterval = setInterval(updateResendTimer, 1000);
    }

    function updateResendTimer() {
        if (resendTimeLeft <= 0) {
            resendTimerElement.style.display = 'none';
            clearInterval(resendTimerInterval);
            return;
        }

        resendCountdownElement.textContent = resendTimeLeft;
        resendTimeLeft--;
    }

    function setupEventListeners() {
        if (verifyForm) {
            verifyForm.addEventListener('submit', async function(e) {
                e.preventDefault();

                const btn = document.getElementById('verifyBtn');
                const btnText = document.getElementById('verifyBtnText') || document.getElementById('btnText');
                const spinner = document.getElementById('verifySpinner') || document.getElementById('spinner');

                const fullCode = hiddenCodeInput.value;
                if (fullCode.length !== 5) {
                    showMessage('Введите все 5 цифр кода', 'error');
                    return;
                }

                if (btnText) btnText.style.display = 'none';
                if (spinner) spinner.style.display = 'inline-block';
                if (btn) btn.disabled = true;
                if (messageEl) messageEl.style.display = 'none';

                try {
                    const formData = new FormData();
                    formData.append('code', fullCode);

                    const endpoint = isResetPassword ? '/verify_reset_code' : '/verify_email';

                    const response = await fetch(endpoint, {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage(result.message, 'success');
                        setTimeout(() => {
                            window.location.href = result.redirect || '/';
                        }, 1500);
                    } else {
                        showMessage(result.message, 'error');

                        if (result.message.includes('Неверный код') ||
                            result.message.includes('истек') ||
                            result.message.includes('попыток')) {
                            resetCodeInputs();
                        }
                    }
                } catch (error) {
                    console.error('Verification error:', error);
                    showMessage('Ошибка сети. Попробуйте еще раз.', 'error');
                } finally {
                    // Восстанавливаем кнопку
                    if (btnText) btnText.style.display = 'inline-block';
                    if (spinner) spinner.style.display = 'none';
                    if (btn) btn.disabled = false;
                }
            });
        }

        if (resendBtn) {
            resendBtn.addEventListener('click', async function() {
                const btn = this;
                const originalText = btn.textContent;
                btn.textContent = 'Отправка...';
                btn.disabled = true;

                try {
                    const endpoint = isResetPassword ? '/resend_reset_code' : '/resend_verification_code';

                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage('Код отправлен повторно', 'success');

                        timeLeft = 15 * 60;
                        updateTimer();
                        if (timerElement) timerElement.classList.remove('expired');

                        resetCodeInputs();

                        startResendTimer();
                    } else {
                        showMessage(result.message, 'error');
                    }
                } catch (error) {
                    console.error('Resend error:', error);
                    showMessage('Ошибка отправки кода', 'error');
                } finally {
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
            });
        }
    }

    function resetCodeInputs() {
        codeInputs.forEach(input => {
            input.value = '';
        });
        updateHiddenCode();
        if (codeInputs.length > 0) {
            codeInputs[0].focus();
        }
    }

    function showMessage(text, type) {
        if (!messageEl) return;

        messageEl.innerHTML = `<div class="${type}">${text}</div>`;
        messageEl.style.display = 'block';

        setTimeout(() => {
            if (messageEl) {
                messageEl.style.display = 'none';
            }
        }, 5000);
    }

    if (codeInputs.length > 0) {
        codeInputs[0].focus();
    }

    if (resendTimerElement && resendTimerElement.style.display !== 'none') {
        startResendTimer();
    }
});

if (!document.querySelector('#verify-email-styles')) {
    const style = document.createElement('style');
    style.id = 'verify-email-styles';
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
        .expired {
            color: #f44336;
            font-weight: bold;
        }
        .timer {
            text-align: center;
            margin: 15px 0;
            font-size: 14px;
            color: #666;
        }
        .code-inputs {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .code-input {
            width: 50px;
            height: 60px;
            text-align: center;
            font-size: 24px;
            border: 2px solid #ddd;
            border-radius: 8px;
            outline: none;
            transition: all 0.3s;
        }
        .code-input:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}