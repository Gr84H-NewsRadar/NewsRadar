// Sources & Channels management

let sourcesCache = [];
let channelsCache = [];
let currentTab = 'sources';

async function loadSources() {
    if (isReader()) {
        const btn = document.getElementById('btn-add-source');
        if (btn) btn.style.display = 'none';
    }
    try {
        sourcesCache = await api.listSources();
        renderSources();

        // Cargar todos los canales agregados
        channelsCache = [];
        for (const s of sourcesCache) {
            try {
                const chs = await api.listChannels(s.id);
                chs.forEach(c => channelsCache.push({ ...c, source_name: s.name }));
            } catch (e) {}
        }
    } catch (err) {
        console.error(err);
    }
}

function renderSources() {
    const list = document.getElementById('sources-list');
    if (!sourcesCache || sourcesCache.length === 0) {
        list.innerHTML = '<p class="text-muted text-center py-4">No hay fuentes configuradas.</p>';
        return;
    }
    list.innerHTML = sourcesCache.map(s => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-3">
            <div>
                <i class="bi bi-globe me-2"></i>
                <strong>${s.name}</strong>
                <small class="text-muted ms-2">${s.url}</small>
            </div>
            <div>
                <a href="${s.url}" target="_blank" class="btn btn-sm btn-light"><i class="bi bi-box-arrow-up-right"></i></a>
                ${!isReader() ? `<button class="btn btn-sm btn-danger" onclick="deleteSource(${s.id})"><i class="bi bi-trash"></i></button>` : ''}
            </div>
        </div>
    `).join('');
}

function renderChannels() {
    const list = document.getElementById('channels-list');
    if (!channelsCache || channelsCache.length === 0) {
        list.innerHTML = '<p class="text-muted text-center py-4">No hay canales RSS.</p>';
        return;
    }
    list.innerHTML = channelsCache.map(c => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
            <div>
                <i class="bi bi-rss me-2"></i>
                <strong>${c.source_name}</strong>
                <small class="text-muted ms-2">${c.url}</small>
                ${c.is_active ? '<span class="badge bg-success ms-2">Activo</span>' : '<span class="badge bg-secondary ms-2">Inactivo</span>'}
            </div>
        </div>
    `).join('');
}

function showTab(tab) {
    currentTab = tab;
    document.getElementById('sources-list').style.display = tab === 'sources' ? 'block' : 'none';
    document.getElementById('channels-list').style.display = tab === 'channels' ? 'block' : 'none';
    if (tab === 'channels') renderChannels();
}

function openSourceModal() {
    document.getElementById('source-form').reset();
    new bootstrap.Modal(document.getElementById('sourceModal')).show();
}

async function saveSource() {
    const data = {
        name: document.getElementById('source-name').value,
        url: document.getElementById('source-url').value
    };
    try {
        await api.createSource(data);
        bootstrap.Modal.getInstance(document.getElementById('sourceModal')).hide();
        loadSources();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function deleteSource(id) {
    if (!confirm('¿Eliminar esta fuente y todos sus canales?')) return;
    try {
        await api.deleteSource(id);
        loadSources();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

function filterList() {
    const term = document.getElementById('filter-input').value.toLowerCase();
    if (currentTab === 'sources') {
        document.querySelectorAll('#sources-list > div').forEach(el => {
            el.style.display = el.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
    } else {
        document.querySelectorAll('#channels-list > div').forEach(el => {
            el.style.display = el.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
    }
}

document.addEventListener('DOMContentLoaded', loadSources);
