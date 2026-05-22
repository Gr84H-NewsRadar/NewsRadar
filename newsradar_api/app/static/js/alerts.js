// Alerts management

let categoriesCache = [];
let channelsCache = [];

async function loadAlerts() {
    const me = await api.getMe();
    localStorage.setItem('user', JSON.stringify(me));

    // Si es lector, ocultar botón de creación
    if (isReader()) {
        const btn = document.getElementById('btn-new-alert');
        if (btn) btn.style.display = 'none';
    }

    // Cargar categorías
    categoriesCache = await api.listCategories();
    channelsCache = await loadRssChannels();
    const sel = document.getElementById('alert-category');
    if (sel) {
        sel.innerHTML = '<option value="">— ninguna —</option>';
        categoriesCache.forEach(c => {
            sel.innerHTML += `<option value="${c.id}|${c.name}">${c.name}</option>`;
        });
    }
    renderChannelOptions();

    // Cargar alertas
    try {
        const alerts = await api.listAlerts(me.id);
        renderAlerts(alerts);
    } catch (err) {
        console.error(err);
    }
}

async function loadRssChannels() {
    const sources = await api.listSources();
    const channels = [];
    for (const source of sources) {
        try {
            const items = await api.listChannels(source.id);
            items.forEach(channel => channels.push({ ...channel, source_name: source.name }));
        } catch (err) {}
    }
    return channels;
}

function renderChannelOptions(selectedIds = []) {
    const sel = document.getElementById('alert-rss-channels');
    if (!sel) return;
    const selected = new Set(selectedIds.map(String));
    sel.innerHTML = channelsCache.map(channel => {
        const isSelected = selected.has(String(channel.id)) ? 'selected' : '';
        return `<option value="${channel.id}" ${isSelected}>${channel.source_name} - ${channel.url}</option>`;
    }).join('');
}

function renderAlerts(alerts) {
    const tbody = document.getElementById('alerts-table');
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No hay alertas configuradas todavía.</td></tr>`;
        return;
    }
    tbody.innerHTML = alerts.map(a => `
        <tr>
            <td><strong>${a.name}</strong></td>
            <td>${(a.descriptors || []).map(d => `<span class="badge bg-secondary me-1">${d}</span>`).join('')}</td>
            <td>${(a.categories || []).map(c => `<span class="badge bg-light text-dark me-1">${c.label}</span>`).join('')}</td>
            <td>${renderAlertChannels(a.rss_channels_ids || [])}</td>
            <td><code>${a.cron_expression}</code></td>
            <td>
                ${!isReader() ? `
                    <button class="btn btn-sm btn-light" onclick='editAlert(${JSON.stringify(a).replace(/'/g, "&#39;")})'><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="deleteAlert(${a.id})"><i class="bi bi-trash"></i></button>
                ` : '<span class="text-muted small">Solo lectura</span>'}
            </td>
        </tr>
    `).join('');
}

function renderAlertChannels(channelIds) {
    if (!channelIds.length) return '<span class="text-muted small">Todos</span>';
    return channelIds.map(id => {
        const channel = channelsCache.find(c => String(c.id) === String(id));
        const label = channel ? channel.source_name : `Canal ${id}`;
        return `<span class="badge bg-info text-dark me-1">${label}</span>`;
    }).join('');
}

function openAlertModal() {
    document.getElementById('alert-id').value = '';
    document.getElementById('alert-form').reset();
    document.getElementById('alert-cron').value = '0 */6 * * *';
    renderChannelOptions();
    new bootstrap.Modal(document.getElementById('alertModal')).show();
}

function editAlert(alert) {
    document.getElementById('alert-id').value = alert.id;
    document.getElementById('alert-name').value = alert.name;
    document.getElementById('alert-descriptors').value = (alert.descriptors || []).join(', ');
    document.getElementById('alert-cron').value = alert.cron_expression;
    if (alert.categories && alert.categories.length > 0) {
        const code = alert.categories[0].code;
        const cat = categoriesCache.find(c => c.code === code);
        if (cat) document.getElementById('alert-category').value = `${cat.id}|${cat.name}`;
    }
    renderChannelOptions(alert.rss_channels_ids || []);
    new bootstrap.Modal(document.getElementById('alertModal')).show();
}

async function saveAlert() {
    const me = JSON.parse(localStorage.getItem('user'));
    const id = document.getElementById('alert-id').value;
    const btn = document.querySelector('#alertModal .btn.btn-dark');
    const stopLoading = setButtonLoading(btn, id ? 'Guardando...' : 'Creando...');
    const descriptors = document.getElementById('alert-descriptors').value
        .split(',').map(s => s.trim()).filter(s => s);

    let categories = [];
    const catVal = document.getElementById('alert-category').value;
    if (catVal) {
        const [catId, catName] = catVal.split('|');
        const cat = categoriesCache.find(c => c.id == catId);
        if (cat) categories = [{ code: cat.code || cat.name.toUpperCase(), label: cat.name }];
    }

    const data = {
        name: document.getElementById('alert-name').value,
        descriptors,
        categories,
        cron_expression: document.getElementById('alert-cron').value,
        notify_email: document.getElementById('notify-email').checked,
        notify_inbox: document.getElementById('notify-inbox').checked,
        rss_channel_ids: Array.from(document.getElementById('alert-rss-channels').selectedOptions)
            .map(option => Number(option.value))
    };

    try {
        if (id) {
            await api.updateAlert(me.id, id, data);
            showToast(`Alerta "${data.name}" actualizada correctamente.`);
            showPopup('Alerta actualizada', `<p class="mb-0">La alerta <strong>${data.name}</strong> se ha actualizado correctamente.</p>`);
        } else {
            await api.createAlert(me.id, data);
            showToast(`Alerta "${data.name}" creada correctamente.`);
            showPopup('Alerta creada', `<p class="mb-0">La alerta <strong>${data.name}</strong> se ha creado correctamente.</p>`);
        }
        bootstrap.Modal.getInstance(document.getElementById('alertModal')).hide();
        loadAlerts();
    } catch (err) {
        showToast('Error al guardar la alerta: ' + err.message, 'error');
    } finally {
        stopLoading();
    }
}

async function deleteAlert(id) {
    if (!confirm('¿Eliminar esta alerta?')) return;
    const me = JSON.parse(localStorage.getItem('user'));
    const row = Array.from(document.querySelectorAll('#alerts-table tr'))
        .find(item => item.innerHTML.includes(`deleteAlert(${id})`));
    const alertName = row ? row.querySelector('strong')?.textContent : 'La alerta';
    try {
        await api.deleteAlert(me.id, id);
        showToast('Alerta eliminada correctamente.');
        showPopup('Alerta eliminada', `<p class="mb-0"><strong>${alertName || 'La alerta'}</strong> se ha eliminado correctamente.</p>`);
        loadAlerts();
    } catch (err) {
        showToast('Error al eliminar la alerta: ' + err.message, 'error');
    }
}

async function suggestSynonyms() {
    const text = document.getElementById('alert-descriptors').value;
    const firstKw = text.split(',')[0].trim();
    if (!firstKw) {
        alert('Escribe al menos una palabra clave primero');
        return;
    }
    const container = document.getElementById('synonym-suggestions');
    container.innerHTML = '<small class="text-muted">Buscando sinónimos...</small>';
    try {
        const data = await api.getSynonyms(firstKw);
        if (!data.synonyms || data.synonyms.length === 0) {
            container.innerHTML = '<small class="text-muted">No se encontraron sinónimos.</small>';
            return;
        }
        container.innerHTML = '<small class="text-muted d-block mb-1">Click para añadir:</small>';
        data.synonyms.forEach(s => {
            const chip = document.createElement('span');
            chip.className = 'synonym-suggestion';
            chip.textContent = s;
            chip.onclick = () => {
                const input = document.getElementById('alert-descriptors');
                const current = input.value.trim();
                input.value = current ? `${current}, ${s}` : s;
                chip.classList.add('selected');
            };
            container.appendChild(chip);
        });
    } catch (err) {
        container.innerHTML = `<small class="text-danger">Error: ${err.message}</small>`;
    }
}

document.addEventListener('DOMContentLoaded', loadAlerts);
