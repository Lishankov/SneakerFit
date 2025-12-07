document.addEventListener('DOMContentLoaded', function() {
    // Элементы DOM
    const codeInputs = document.querySelectorAll('.code-input');
    const hiddenCodeInput = document.getElementById('verificationCode');
    const verifyForm = document.getElementById('verifyForm');
    const resendBtn = document.getElementById('resendBtn');
    const messageEl = document.getElementById('message');
    const timerElement = document.getElementById('timer');
    const resendTimerElement = document.getElementById('resendTimer');
    const resendCountdownElement = document.getElementById('resendCountdown');

    // Таймер для кода
    let timeLeft = 15 * 60; // 15 минут в секундах
    let timerInterval;

    // Таймер для повторной отправки
    let resendTimeLeft = 60;
    let resendTimerInterval;

    // Инициализация
    initCodeInputs();
    startTimer();
    setupEventListeners();

    function initCodeInputs() {
        // Настройка ввода кода
        codeInputs.forEach((input, index) => {
            input.addEventListener('input', function(e) {
                // Проверяем, что введена цифра
                if (this.value && !/^\d$/.test(this.value)) {
                    this.value = '';
                    return;
                }

                // Обновляем скрытое поле
                updateHiddenCode();

                // Переход к следующему полю
                if (this.value && index < codeInputs.length - 1) {
                    codeInputs[index + 1].focus();
                }
            });

            input.addEventListener('keydown', function(e) {
                // Обработка Backspace и Delete
                if (e.key === 'Backspace' && !this.value && index > 0) {
                    codeInputs[index - 1].focus();
                }

                // Перемещение стрелками
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
        // Обработка формы подтверждения
        if (verifyForm) {
            verifyForm.addEventListener('submit', async function(e) {
                e.preventDefault();

                const btn = document.getElementById('verifyBtn');
                const btnText = document.getElementById('verifyBtnText');
                const spinner = document.getElementById('verifySpinner');

                // Проверяем, что все поля заполнены
                const fullCode = hiddenCodeInput.value;
                if (fullCode.length !== 5) {
                    showMessage('Введите все 5 цифр кода', 'error');
                    return;
                }

                // Отключаем кнопку и показываем спиннер
                btnText.style.display = 'none';
                spinner.style.display = 'inline-block';
                btn.disabled = true;
                messageEl.style.display = 'none';

                try {
                    const formData = new FormData();
                    formData.append('code', fullCode);

                    const response = await fetch('/verify_email', {
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

                        // Очищаем поля при ошибке
                        if (result.message.includes('Неверный код') || result.message.includes('истек')) {
                            resetCodeInputs();
                        }
                    }
                } catch (error) {
                    console.error('Verification error:', error);
                    showMessage('Ошибка сети. Попробуйте еще раз.', 'error');
                } finally {
                    // Восстанавливаем кнопку
                    btnText.style.display = 'inline-block';
                    spinner.style.display = 'none';
                    btn.disabled = false;
                }
            });
        }

        // Обработка повторной отправки кода
        if (resendBtn) {
            resendBtn.addEventListener('click', async function() {
                const btn = this;
                const originalText = btn.textContent;
                btn.textContent = 'Отправка...';
                btn.disabled = true;

                try {
                    const response = await fetch('/resend_verification_code', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage('Код отправлен повторно', 'success');

                        // Сбрасываем таймер
                        timeLeft = 15 * 60;
                        updateTimer();
                        timerElement.classList.remove('expired');

                        // Очищаем поля ввода
                        resetCodeInputs();

                        // Запускаем таймер повторной отправки
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
        codeInputs[0].focus();
    }

    function showMessage(text, type) {
        messageEl.innerHTML = `<div class="${type}">${text}</div>`;
        messageEl.style.display = 'block';

        // Автоматически скрываем сообщение через 5 секунд
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }

    // Фокус на первое поле при загрузке
    if (codeInputs.length > 0) {
        codeInputs[0].focus();
    }
});