// Sources & Channels management

let sourcesCache = [];
let channelsCache = [];
let categoriesCache = [];
let currentTab = 'sources';

async function loadSources() {
    if (isReader()) {
        const btn = document.getElementById('btn-add-source');
        if (btn) btn.style.display = 'none';
        const channelBtn = document.getElementById('btn-add-channel');
        if (channelBtn) channelBtn.style.display = 'none';
        const processBtn = document.getElementById('btn-process-rss');
        if (processBtn) processBtn.style.display = 'none';
    }
    try {
        categoriesCache = await api.listCategories();
        sourcesCache = (await api.listSources())
            .sort((a, b) => Number(b.id) - Number(a.id));

        channelsCache = [];
        for (const s of sourcesCache) {
            try {
                const chs = await api.listChannels(s.id);
                chs.forEach(c => channelsCache.push({ ...c, source_name: s.name }));
            } catch (e) {}
        }
        channelsCache.sort((a, b) => Number(b.id) - Number(a.id));
        renderSources();
        renderChannels();
        filterList();
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
        <div class="source-row d-flex justify-content-between align-items-center border-bottom py-3">
            <div>
                <i class="bi bi-globe me-2"></i>
                <strong>${s.name}</strong>
                <small class="text-muted ms-2">${s.url}</small>
            </div>
            <div>
                <a href="${s.url}" target="_blank" class="btn btn-sm btn-light"><i class="bi bi-box-arrow-up-right"></i></a>
                ${!isReader() ? `<button type="button" class="btn btn-sm btn-danger" id="delete-source-${s.id}" onclick="deleteSource(${s.id}, '${escapeForInline(s.name)}')"><i class="bi bi-trash"></i></button>` : ''}
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
        <div class="channel-row d-flex justify-content-between align-items-center border-bottom py-2">
            <div>
                <i class="bi bi-rss me-2"></i>
                <strong>${c.source_name}</strong>
                <small class="text-muted ms-2">${c.url}</small>
                <span class="badge bg-light text-dark ms-2">${getCategoryName(c.category_id)}</span>
                ${c.is_active === false ? '<span class="badge bg-secondary ms-2">Inactivo</span>' : '<span class="badge bg-success ms-2">Activo</span>'}
            </div>
        </div>
    `).join('');
}

function getCategoryName(categoryId) {
    const cat = categoriesCache.find(c => Number(c.id) === Number(categoryId));
    return cat ? cat.name : `Categoría ${categoryId}`;
}

function escapeForInline(value) {
    return String(value || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function showTab(tab) {
    currentTab = tab;
    document.getElementById('sources-list').style.display = tab === 'sources' ? 'block' : 'none';
    document.getElementById('channels-list').style.display = tab === 'channels' ? 'block' : 'none';
    if (tab === 'channels') renderChannels();
    filterList();
}

function openSourceModal() {
    document.getElementById('source-form').reset();
    new bootstrap.Modal(document.getElementById('sourceModal')).show();
}

function openChannelModal() {
    if (!sourcesCache.length) {
        alert('Crea una fuente antes de añadir un canal RSS.');
        return;
    }
    document.getElementById('channel-form').reset();
    const sourceSelect = document.getElementById('channel-source');
    const categorySelect = document.getElementById('channel-category');

    sourceSelect.innerHTML = sourcesCache
        .map(s => `<option value="${s.id}">${s.name}</option>`)
        .join('');
    categorySelect.innerHTML = categoriesCache
        .map(c => `<option value="${c.id}">${c.name}</option>`)
        .join('');

    syncChannelUrl();
    new bootstrap.Modal(document.getElementById('channelModal')).show();
}

function syncChannelUrl() {
    const sourceId = Number(document.getElementById('channel-source').value);
    const source = sourcesCache.find(s => Number(s.id) === sourceId);
    if (source) document.getElementById('channel-url').value = source.url;
}

async function saveSource() {
    const btn = document.querySelector('#sourceModal .btn.btn-dark');
    const stopLoading = setButtonLoading(btn, 'Guardando...');
    const data = {
        name: document.getElementById('source-name').value,
        url: document.getElementById('source-url').value
    };
    try {
        const source = await api.createSource(data);
        bootstrap.Modal.getInstance(document.getElementById('sourceModal')).hide();
        showToast(`Fuente "${source.name}" guardada correctamente.`);
        showPopup('Fuente guardada', `<p class="mb-0">La fuente <strong>${source.name}</strong> se ha guardado correctamente.</p>`);
        setPageStatus('sources-status', `<i class="bi bi-check-circle"></i><span>Fuente "${source.name}" guardada correctamente.</span>`, 'success');
        await loadSources();
        showTab('sources');
    } catch (err) {
        showToast('Error al guardar la fuente: ' + err.message, 'error');
    } finally {
        stopLoading();
    }
}

async function saveChannel() {
    const btn = document.querySelector('#channelModal .btn.btn-dark');
    const stopLoading = setButtonLoading(btn, 'Guardando...');
    const sourceId = Number(document.getElementById('channel-source').value);
    const data = {
        url: document.getElementById('channel-url').value,
        category_id: Number(document.getElementById('channel-category').value)
    };
    try {
        const channel = await api.createChannel(sourceId, data);
        bootstrap.Modal.getInstance(document.getElementById('channelModal')).hide();
        showToast('Canal RSS guardado correctamente.');
        showPopup('Canal RSS guardado', `<p class="mb-0">El canal RSS se ha guardado correctamente para <strong>${channel.url}</strong>.</p>`);
        setPageStatus('sources-status', `<i class="bi bi-check-circle"></i><span>Canal RSS guardado para ${channel.url}.</span>`, 'success');
        currentTab = 'channels';
        await loadSources();
        showTab('channels');
    } catch (err) {
        showToast('Error al guardar el canal: ' + err.message, 'error');
    } finally {
        stopLoading();
    }
}

async function deleteSource(id, name = 'esta fuente') {
    const sourceName = name || 'esta fuente';
    if (!window.confirm(`¿Eliminar "${sourceName}" y todos sus canales RSS?`)) return;

    const btn = document.getElementById(`delete-source-${id}`);
    const stopLoading = setButtonLoading(btn, '');
    try {
        await api.deleteSource(id);
        showToast(`Fuente "${sourceName}" eliminada correctamente.`);
        setPageStatus('sources-status', `<i class="bi bi-check-circle"></i><span>Fuente "${sourceName}" eliminada correctamente.</span>`, 'success');
        await loadSources();
        showTab(currentTab);
    } catch (err) {
        showToast('Error al eliminar la fuente: ' + err.message, 'error');
        setPageStatus('sources-status', `<i class="bi bi-exclamation-triangle"></i><span>No se pudo eliminar la fuente: ${err.message}</span>`, 'error');
    } finally {
        stopLoading();
    }
}

async function processRssNow() {
    const btn = document.getElementById('btn-process-rss');
    const stopLoading = setButtonLoading(btn, 'Procesando...');
    try {
        setPageStatus('sources-status', '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Procesando canales RSS. Esto puede tardar unos segundos...</span>', 'info');
        const result = await api.processRss();
        if (result.status === 'busy') {
            const busyMessage = 'Ya hay un procesado RSS en marcha. Espera unos segundos y vuelve a intentarlo.';
            setPageStatus('sources-status', `<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>${busyMessage}</span>`, 'info');
            showToast(busyMessage, 'info');
            return;
        }
        const stats = result.statistics || {};
        const summaries = stats.alert_summaries || [];
        const totalNews = stats.total_news_items || 0;
        const totalMatches = stats.total_alerts_triggered || 0;
        let summaryText = '';
        if (summaries.length) {
            summaryText = summaries.map(item => `${item.alert_name}: ${item.matches_count} noticias coincidentes`).join('; ');
        } else if (totalNews > 0) {
            summaryText = `Se leyeron ${totalNews} noticias del RSS, pero ninguna coincide con tus alertas activas`;
        } else {
            summaryText = 'No se encontraron noticias nuevas en esta ejecución';
        }
        const message = `Procesado completado. Noticias leídas: ${totalNews}. Coincidencias: ${totalMatches}. ${summaryText}.`;
        setPageStatus('sources-status', `<i class="bi bi-check-circle"></i><span>${message}</span>`, 'success');
        showToast(message, 'success', 6500);
        showPopup(
            'Procesado RSS completado',
            `<p>${message}</p><p class="mb-0">Puedes revisar el detalle en tu correo o en el apartado de notificaciones.</p>`,
            [
                { label: 'Abrir correo', className: 'btn-outline-dark', onClick: () => { window.open('http://localhost:8025', '_blank'); } },
                { label: 'Ver notificaciones', className: 'btn-dark', onClick: () => { window.location.href = '/static/notifications.html'; } },
                { label: 'Buscar noticias', className: 'btn-outline-dark', onClick: () => { window.location.href = '/static/search.html'; } },
                { label: 'Cerrar', className: 'btn-light' }
            ]
        );
    } catch (err) {
        setPageStatus('sources-status', `<i class="bi bi-exclamation-triangle"></i><span>Error al procesar RSS: ${err.message}</span>`, 'error');
        showToast('Error al procesar RSS: ' + err.message, 'error');
    } finally {
        stopLoading();
    }
}

function filterList() {
    const input = document.getElementById('filter-input');
    const term = (input?.value || '').trim().toLowerCase();
    const listId = currentTab === 'sources' ? 'sources-list' : 'channels-list';
    const rowSelector = currentTab === 'sources' ? '.source-row' : '.channel-row';
    const list = document.getElementById(listId);
    if (!list) return;

    list.querySelectorAll('.filter-empty').forEach(el => el.remove());
    const rows = Array.from(list.querySelectorAll(rowSelector));
    let visibleCount = 0;

    rows.forEach(el => {
        const visible = !term || el.textContent.toLowerCase().includes(term);
        el.style.display = visible ? '' : 'none';
        if (visible) visibleCount += 1;
    });

    if (rows.length > 0 && visibleCount === 0) {
        const empty = document.createElement('p');
        empty.className = 'filter-empty text-muted text-center py-4 mb-0';
        empty.textContent = 'No hay resultados para ese filtro.';
        list.appendChild(empty);
    }
}

document.addEventListener('DOMContentLoaded', loadSources);
