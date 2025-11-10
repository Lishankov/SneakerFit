async function loadRecommendations() {
    try {
        const response = await fetch('/get_recommendations');
        const recommendations = await response.json();

        const container = document.getElementById('recommendations-container');

        if (recommendations.error) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <p>Пожалуйста, войдите в систему</p>
                    <a href="/loggin" class="btn btn-primary">Войти</a>
                </div>
            `;
            return;
        }

        if (recommendations.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <p>Для получения рекомендаций необходимо заполнить измерения стопы</p>
                    <a href="/measure" class="btn btn-primary">Заполнить измерения</a>
                </div>
            `;
            return;
        }

        let html = '<div class="recommendations-grid">';

        for (const rec of recommendations) {
            const imageUrl = getShoeImageUrl(rec.model);

            const imageExists = await new Promise(resolve => {
                checkImageExists(imageUrl, resolve);
            });

            const finalImageUrl = imageExists ? imageUrl :
                "https://via.placeholder.com/250x200/4285f4/ffffff?text=" + encodeURIComponent(rec.model.split(' ')[0]);

            const compatibilityColor = getCompatibilityColor(rec.compatibility);

            html += `
                <div class="shoe-card">
                    <div class="shoe-image">
                        <img src="${finalImageUrl}" alt="${rec.model}"
                             onerror="this.src='https://via.placeholder.com/250x200/4285f4/ffffff?text='+encodeURIComponent('${rec.model.split(' ')[0]}')">
                    </div>
                    <div class="shoe-model">${rec.model}</div>
                    <div class="compatibility-badge" style="background: ${compatibilityColor}">
                        Совместимость: ${rec.compatibility}%
                    </div>
                    <div class="size-info">
                        Рекомендуемый размер: <strong>EU ${rec.best_size.eu}</strong>
                    </div>
                    <a href="/shoe/${encodeURIComponent(rec.model)}">
                        <button class="nav-btn" style="margin-top: 10px;">Подробнее</button>
                    </a>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading recommendations:', error);
        document.getElementById('recommendations-container').innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <p>Ошибка загрузки рекомендаций</p>
                <button onclick="loadRecommendations()" class="btn btn-primary">Попробовать снова</button>
            </div>
        `;
    }
}

function getShoeImageUrl(modelName) {
    return `/static/models%20photo/${encodeURIComponent(modelName)}/1.jpg`;
}

function checkImageExists(url, callback) {
    const img = new Image();
    img.onload = function() {
        callback(true);
    };
    img.onerror = function() {
        callback(false);
    };
    img.src = url;
}

function getCompatibilityColor(percentage) {
    if (percentage >= 80) return '#4CAF50';
    if (percentage >= 60) return '#FF9800';
    return '#F44336';
}

document.addEventListener('DOMContentLoaded', loadRecommendations);