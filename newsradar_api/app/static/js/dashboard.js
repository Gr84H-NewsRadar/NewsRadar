// Dashboard - estadísticas globales (RF13)

async function loadDashboard() {
    try {
        const me = await api.getMe();
        document.getElementById('user-info').textContent = `${me.first_name} ${me.last_name}`;
        localStorage.setItem('user', JSON.stringify(me));

        const stats = await api.getDashboardStats();
        document.getElementById('kpi-sources').textContent = stats.total_sources || 0;
        document.getElementById('kpi-news').textContent = stats.total_news || 0;
        document.getElementById('kpi-alerts').textContent = stats.total_alerts || 0;

        // total channels = sumamos todos los canales de todas las sources
        const sources = await api.listSources();
        let totalChannels = 0;
        for (const s of sources) {
            try {
                const chs = await api.listChannels(s.id);
                totalChannels += chs.length;
            } catch (e) {}
        }
        document.getElementById('kpi-channels').textContent = totalChannels;

        // Bar chart: noticias por categoría
        const catLabels = Object.keys(stats.news_by_category || {});
        const catValues = Object.values(stats.news_by_category || {});
        new Chart(document.getElementById('bar-chart'), {
            type: 'bar',
            data: {
                labels: catLabels,
                datasets: [{ label: 'Noticias', data: catValues, backgroundColor: '#212529' }]
            },
            options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
        });

        // Lista de categorías
        const list = document.getElementById('category-list');
        if (list) {
            list.innerHTML = '';
            catLabels.forEach((label, i) => {
                const li = document.createElement('li');
                li.className = 'd-flex justify-content-between border-bottom py-1';
                li.innerHTML = `<span>${label.toUpperCase()}</span><strong>${catValues[i]}</strong>`;
                list.appendChild(li);
            });
        }

        // Line chart: simulamos evolución (a partir de stats globales) — en producción haría un endpoint /stats/timeline
        const days = ['01', '02', '03', '04', '05', '06', '07'].map(d => d + ' Mar');
        const baseValue = Math.max(stats.total_news || 0, 100);
        const lineData = days.map(() => Math.floor(baseValue / 7 * (0.7 + Math.random() * 0.6)));
        new Chart(document.getElementById('line-chart'), {
            type: 'line',
            data: {
                labels: days,
                datasets: [{ label: 'Noticias/día', data: lineData, borderColor: '#212529', tension: 0.3 }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    } catch (err) {
        console.error('Error cargando dashboard:', err);
    }
}

// Búsqueda rápida desde la barra
document.getElementById('search-bar')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const q = e.target.value.trim();
        if (q) window.location.href = `/static/search.html?q=${encodeURIComponent(q)}`;
    }
});

document.addEventListener('DOMContentLoaded', loadDashboard);
