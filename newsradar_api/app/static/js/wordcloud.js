// Word cloud (RF14)

async function loadWordClouds() {
    try {
        // Global
        const global = await api.getWordCloud();
        renderCloud('cloud-global', global.words || []);

        // Por categoría
        const categories = await api.listCategories();
        const container = document.getElementById('cloud-by-category');
        for (const cat of categories) {
            const data = await api.getWordCloud(cat.id);
            if (!data.words || data.words.length === 0) continue;

            const col = document.createElement('div');
            col.className = 'col-md-6';
            col.innerHTML = `
                <div class="card shadow-sm">
                    <div class="card-body">
                        <h6 class="text-muted small">${cat.name.toUpperCase()}</h6>
                        <div id="cloud-cat-${cat.id}" class="word-cloud-container" style="min-height:140px;"></div>
                    </div>
                </div>
            `;
            container.appendChild(col);
            renderCloud(`cloud-cat-${cat.id}`, data.words);
        }
    } catch (err) {
        console.error('Error cargando word clouds:', err);
        document.getElementById('cloud-global').innerHTML =
            '<p class="text-muted">No hay suficientes datos para generar la nube de palabras todavía. Procesa algunos canales RSS primero.</p>';
    }
}

function renderCloud(containerId, words) {
    const el = document.getElementById(containerId);
    if (!el || !words || words.length === 0) {
        if (el) el.innerHTML = '<p class="text-muted small">No hay datos.</p>';
        return;
    }

    // Render alternativo en texto (rápido y robusto)
    const max = Math.max(...words.map(w => w[1]));
    const min = Math.min(...words.map(w => w[1]));
    el.innerHTML = '';
    el.style.lineHeight = '2';
    words.forEach(([word, count]) => {
        const size = 0.8 + ((count - min) / Math.max(max - min, 1)) * 2.2;
        const span = document.createElement('span');
        span.className = 'word-cloud-tag';
        span.style.fontSize = size + 'rem';
        span.textContent = word.toUpperCase();
        el.appendChild(span);
    });
}

document.addEventListener('DOMContentLoaded', loadWordClouds);
