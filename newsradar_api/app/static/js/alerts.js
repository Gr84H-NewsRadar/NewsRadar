// Alerts management

let categoriesCache = [];

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
    const sel = document.getElementById('alert-category');
    if (sel) {
        sel.innerHTML = '<option value="">— ninguna —</option>';
        categoriesCache.forEach(c => {
            sel.innerHTML += `<option value="${c.id}|${c.name}">${c.name}</option>`;
        });
    }

    // Cargar alertas
    try {
        const alerts = await api.listAlerts(me.id);
        renderAlerts(alerts);
    } catch (err) {
        console.error(err);
    }
}

function renderAlerts(alerts) {
    const tbody = document.getElementById('alerts-table');
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No hay alertas configuradas todavía.</td></tr>`;
        return;
    }
    tbody.innerHTML = alerts.map(a => `
        <tr>
            <td><strong>${a.name}</strong></td>
            <td>${(a.descriptors || []).map(d => `<span class="badge bg-secondary me-1">${d}</span>`).join('')}</td>
            <td>${(a.categories || []).map(c => `<span class="badge bg-light text-dark me-1">${c.label}</span>`).join('')}</td>
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

function openAlertModal() {
    document.getElementById('alert-id').value = '';
    document.getElementById('alert-form').reset();
    document.getElementById('alert-cron').value = '0 */6 * * *';
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
    new bootstrap.Modal(document.getElementById('alertModal')).show();
}

async function saveAlert() {
    const me = JSON.parse(localStorage.getItem('user'));
    const id = document.getElementById('alert-id').value;
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
        notify_inbox: document.getElementById('notify-inbox').checked
    };

    try {
        if (id) {
            await api.updateAlert(me.id, id, data);
        } else {
            await api.createAlert(me.id, data);
        }
        bootstrap.Modal.getInstance(document.getElementById('alertModal')).hide();
        loadAlerts();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function deleteAlert(id) {
    if (!confirm('¿Eliminar esta alerta?')) return;
    const me = JSON.parse(localStorage.getItem('user'));
    try {
        await api.deleteAlert(me.id, id);
        loadAlerts();
    } catch (err) {
        alert('Error: ' + err.message);
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
