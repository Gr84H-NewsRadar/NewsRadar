// API client - wrapper alrededor de fetch

const API_BASE = '/api/v1';

const api = {
    _token: () => localStorage.getItem('access_token'),

    _headers: (auth = true) => {
        const h = { 'Content-Type': 'application/json' };
        if (auth && api._token()) h['Authorization'] = `Bearer ${api._token()}`;
        return h;
    },

    _handle: async (resp) => {
        if (resp.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/static/index.html';
            throw new Error('Sesión expirada');
        }
        if (!resp.ok) {
            let msg = `Error ${resp.status}`;
            try {
                const data = await resp.json();
                msg = data.detail || msg;
            } catch (e) {}
            throw new Error(msg);
        }
        if (resp.status === 204) return null;
        return resp.json();
    },

    // Auth
    login: async (email, password) => {
        const resp = await fetch(`${API_BASE}/auth/login-json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        return api._handle(resp);
    },

    register: async (data) => {
        const resp = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return api._handle(resp);
    },

    getMe: async () => {
        const resp = await fetch(`${API_BASE}/auth/me`, { headers: api._headers() });
        return api._handle(resp);
    },

    // Users
    updateUser: async (userId, data) => {
        const resp = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'PUT', headers: api._headers(), body: JSON.stringify(data)
        });
        return api._handle(resp);
    },

    // Categories
    listCategories: async () => {
        const resp = await fetch(`${API_BASE}/categories`, { headers: api._headers() });
        return api._handle(resp);
    },

    // Sources
    listSources: async () => {
        const resp = await fetch(`${API_BASE}/information-sources`, { headers: api._headers() });
        return api._handle(resp);
    },

    createSource: async (data) => {
        const resp = await fetch(`${API_BASE}/information-sources`, {
            method: 'POST', headers: api._headers(), body: JSON.stringify(data)
        });
        return api._handle(resp);
    },

    deleteSource: async (id) => {
        const resp = await fetch(`${API_BASE}/information-sources/${id}`, {
            method: 'DELETE', headers: api._headers()
        });
        return api._handle(resp);
    },

    listChannels: async (sourceId) => {
        const resp = await fetch(`${API_BASE}/information-sources/${sourceId}/rss-channels`, {
            headers: api._headers()
        });
        return api._handle(resp);
    },

    // Alerts
    listAlerts: async (userId) => {
        const resp = await fetch(`${API_BASE}/users/${userId}/alerts`, { headers: api._headers() });
        return api._handle(resp);
    },

    createAlert: async (userId, data) => {
        const resp = await fetch(`${API_BASE}/users/${userId}/alerts`, {
            method: 'POST', headers: api._headers(), body: JSON.stringify(data)
        });
        return api._handle(resp);
    },

    updateAlert: async (userId, alertId, data) => {
        const resp = await fetch(`${API_BASE}/users/${userId}/alerts/${alertId}`, {
            method: 'PUT', headers: api._headers(), body: JSON.stringify(data)
        });
        return api._handle(resp);
    },

    deleteAlert: async (userId, alertId) => {
        const resp = await fetch(`${API_BASE}/users/${userId}/alerts/${alertId}`, {
            method: 'DELETE', headers: api._headers()
        });
        return api._handle(resp);
    },

    // Notifications
    listNotifications: async (userId, alertId) => {
        const resp = await fetch(`${API_BASE}/users/${userId}/alerts/${alertId}/notifications`, {
            headers: api._headers()
        });
        return api._handle(resp);
    },

    listAllNotifications: async (userId) => {
        // Recoger notificaciones de todas las alertas del usuario
        const alerts = await api.listAlerts(userId);
        const all = [];
        for (const a of alerts) {
            try {
                const ns = await api.listNotifications(userId, a.id);
                ns.forEach(n => all.push({ ...n, alert_name: a.name }));
            } catch (e) {}
        }
        return all.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    },

    // News & Search (RF17)
    searchNews: async (params) => {
        const qs = new URLSearchParams();
        if (params.q) qs.set('q', params.q);
        if (params.category_id) qs.set('category_id', params.category_id);
        if (params.from) qs.set('date_from', params.from);
        if (params.to) qs.set('date_to', params.to);
        qs.set('limit', params.limit || 50);
        const resp = await fetch(`${API_BASE}/news?${qs.toString()}`, { headers: api._headers() });
        return api._handle(resp);
    },

    // Synonyms (RF04)
    getSynonyms: async (keyword) => {
        const resp = await fetch(`${API_BASE}/synonyms?keyword=${encodeURIComponent(keyword)}`, {
            headers: api._headers()
        });
        return api._handle(resp);
    },

    // Dashboard stats (RF13)
    getDashboardStats: async () => {
        const resp = await fetch(`${API_BASE}/dashboard/stats`, { headers: api._headers() });
        return api._handle(resp);
    },

    // Word cloud (RF14)
    getWordCloud: async (categoryId = null) => {
        const url = categoryId
            ? `${API_BASE}/dashboard/wordcloud?category_id=${categoryId}`
            : `${API_BASE}/dashboard/wordcloud`;
        const resp = await fetch(url, { headers: api._headers() });
        return api._handle(resp);
    },

    // Roles
    listRoles: async () => {
        const resp = await fetch(`${API_BASE}/roles`, { headers: api._headers() });
        return api._handle(resp);
    }
};

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/static/index.html';
}

function requireAuth() {
    if (!api._token()) {
        window.location.href = '/static/index.html';
    }
}

function getCurrentUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function isReader() {
    const u = getCurrentUser();
    if (!u || !u.roles) return true;
    return !u.roles.some(r => ['admin', 'manager'].includes(r.name));
}

// Auto-protect non-public pages
if (!window.location.pathname.includes('index.html') && !window.location.pathname.includes('register.html')) {
    requireAuth();
}
