async function loadProfileRecommendations() {
    try {
        const response = await fetch('/get_recommendations');
        const recommendations = await response.json();

        const container = document.getElementById('profile-recommendations');

        if (recommendations.error || recommendations.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <p>Заполните измерения стопы для получения рекомендаций</p>
                    <a href="/measure" class="btn btn-secondary" style="margin-top: 10px;">Заполнить измерения</a>
                </div>
            `;
            return;
        }

        let html = '<div class="rec-grid">';

        recommendations.slice(0, 3).forEach(rec => {
            html += `
                <div class="rec-card">
                    <div class="rec-title">${rec.model}</div>
                    <div style="font-size: 14px; color: #666;">Совместимость: ${rec.compatibility}%</div>
                    <div style="font-size: 12px; color: #888;">Размер: EU ${rec.best_size.eu}</div>
                    <a href="/shoe/${encodeURIComponent(rec.model)}" class="btn btn-secondary">Подробнее</a>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading profile recommendations:', error);
        document.getElementById('profile-recommendations').innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <p>Ошибка загрузки рекомендаций</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', loadProfileRecommendations);