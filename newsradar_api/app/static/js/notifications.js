// Notifications inbox

async function loadNotifications() {
    const me = await api.getMe();
    const list = document.getElementById('notifications-list');
    try {
        const notifs = await api.listAllNotifications(me.id);
        if (!notifs || notifs.length === 0) {
            list.innerHTML = '<p class="text-muted text-center py-4">No tienes notificaciones todavía.</p>';
            return;
        }
        list.innerHTML = notifs.map(n => {
            const ts = new Date(n.timestamp).toLocaleString();
            const metricsTxt = (n.metrics || []).map(m => `${m.name}: ${m.value}`).join(' · ');
            return `
                <div class="notification-card alert">
                    <div class="d-flex justify-content-between">
                        <strong>Actualización de "${n.alert_name || 'Alerta'}" en ${ts}</strong>
                        <small class="text-muted">${ts}</small>
                    </div>
                    <p class="mb-0 small">${metricsTxt || 'Sin métricas registradas'}</p>
                </div>
            `;
        }).join('');
        await api.markNotificationsRead(me.id);
    } catch (err) {
        list.innerHTML = `<p class="text-danger">Error: ${err.message}</p>`;
    }
}

document.addEventListener('DOMContentLoaded', loadNotifications);
