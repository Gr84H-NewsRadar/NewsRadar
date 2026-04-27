// Search and filter (RF17)

async function init() {
    const cats = await api.listCategories();
    const sel = document.getElementById('filter-category');
    cats.forEach(c => {
        sel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });

    // Si viene ?q=algo en la URL, prellenar y buscar
    const params = new URLSearchParams(window.location.search);
    if (params.has('q')) {
        document.getElementById('filter-q').value = params.get('q');
        doSearch();
    }
}

async function doSearch() {
    const params = {
        q: document.getElementById('filter-q').value.trim(),
        category_id: document.getElementById('filter-category').value,
        from: document.getElementById('filter-from').value,
        to: document.getElementById('filter-to').value
    };

    const list = document.getElementById('results-list');
    const count = document.getElementById('results-count');
    list.innerHTML = '<p class="text-muted">Buscando...</p>';

    try {
        const news = await api.searchNews(params);
        count.textContent = `${news.length} resultado(s)`;
        if (news.length === 0) {
            list.innerHTML = '<p class="text-muted text-center py-4">No se encontraron noticias con esos filtros.</p>';
            return;
        }
        list.innerHTML = news.map(n => {
            const date = n.published_date ? new Date(n.published_date).toLocaleString() : 'Sin fecha';
            const matched = (n.matched_keywords || []).map(k => `<span class="badge bg-warning text-dark me-1">${k}</span>`).join('');
            return `
                <div class="news-result-card">
                    <div class="d-flex justify-content-between">
                        <h6 class="mb-1"><a href="${n.link}" target="_blank">${n.title}</a></h6>
                        <small class="text-muted">${date}</small>
                    </div>
                    ${matched ? `<div class="mb-2">${matched}</div>` : ''}
                    <p class="text-muted small mb-0">${(n.description || '').substring(0, 200)}...</p>
                </div>
            `;
        }).join('');
    } catch (err) {
        list.innerHTML = `<p class="text-danger">Error: ${err.message}</p>`;
    }
}

function clearFilters() {
    document.getElementById('filter-q').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-from').value = '';
    document.getElementById('filter-to').value = '';
    document.getElementById('results-list').innerHTML = '';
    document.getElementById('results-count').textContent = '—';
}

document.addEventListener('DOMContentLoaded', init);
