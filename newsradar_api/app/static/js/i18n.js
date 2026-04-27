// i18n - Internationalization ES/EN

const translations = {
    es: {
        welcome: 'BIENVENIDO',
        welcome_sub: 'Accede a tu panel de control',
        email: 'EMAIL',
        password: 'CONTRASEÑA',
        enter: 'ENTRAR AL SISTEMA →',
        no_account: '¿No tienes cuenta? Regístrate aquí',
        have_account: '¿Ya tienes cuenta? Inicia sesión',
        join: 'ÚNETE A LA RED',
        join_sub: 'Crea tu cuenta de analista',
        firstname: 'NOMBRE',
        lastname: 'APELLIDOS',
        organization: 'ORGANIZACIÓN',
        create: 'CREAR MI CUENTA →',
        dashboard: 'Dashboard',
        dashboard_title: 'Dashboard',
        resumen: 'Resumen',
        resumen_title: 'Resumen — Nube de Descriptores',
        alerts: 'Alertas',
        alerts_title: 'Gestión de Alertas',
        alerts_sub: 'Configura tus radares de información personalizados',
        new_alert: 'Nueva Alerta',
        create_alert: 'CREAR NUEVA ALERTA',
        alert_name: 'NOMBRE DE LA ALERTA',
        descriptors: 'DESCRIPTORES',
        descriptors_csv: 'DESCRIPTORES (separados por coma)',
        categories: 'CATEGORÍAS',
        cron: 'PERIODICIDAD',
        cron_label: 'PERIODICIDAD (CRON)',
        actions: 'ACCIONES',
        suggest: 'Sugerir sinónimos (IA)',
        notify_email: 'Notificar por correo',
        notify_inbox: 'Notificar al buzón',
        cancel: 'CANCELAR',
        save: 'GUARDAR',
        save_alert: 'GUARDAR ALERTA',
        sources: 'Fuentes y RSS',
        sources_title: 'Fuentes e Información',
        sources_tab: 'FUENTES',
        channels_tab: 'CANALES RSS',
        add_source: 'Añadir Fuente',
        add_source_title: 'AÑADIR FUENTE',
        source_name: 'NOMBRE DE LA FUENTE',
        source_url: 'URL',
        notifications: 'Notificaciones',
        inbox_title: 'Buzón de Notificaciones',
        inbox_sub: 'Mensajes y alertas del sistema',
        search: 'Búsqueda',
        search_title: 'Búsqueda y Filtrado de Noticias',
        search_sub: 'Filtra y busca en todas las noticias capturadas',
        search_keyword: 'Palabra clave',
        filter_category: 'Categoría',
        filter_from: 'Desde',
        filter_to: 'Hasta',
        search_btn: 'Buscar',
        search_news: 'Buscar noticias...',
        clear: 'Limpiar',
        profile: 'Perfil',
        profile_title: 'Mi Perfil',
        personal_info: 'INFORMACIÓN PERSONAL',
        edit_profile: 'EDITAR PERFIL',
        security: 'SEGURIDAD',
        change_password: 'Cambiar Contraseña',
        roles_perms: 'ROLES Y PERMISOS',
        logout: 'Cerrar Sesión',
        active_sources: 'FUENTES ACTIVAS',
        captured_news: 'NOTICIAS CAPTURADAS',
        configured_alerts: 'ALERTAS CONFIGURADAS',
        rss_channels: 'CANALES RSS',
        capture_evolution: 'Evolución de Captura',
        news_per_day: 'Volumen de noticias por día',
        news_by_category: 'Noticias por Categoría'
    },
    en: {
        welcome: 'WELCOME',
        welcome_sub: 'Access your control panel',
        email: 'EMAIL',
        password: 'PASSWORD',
        enter: 'LOG IN →',
        no_account: 'No account? Sign up here',
        have_account: 'Already have an account? Sign in',
        join: 'JOIN THE NETWORK',
        join_sub: 'Create your analyst account',
        firstname: 'FIRST NAME',
        lastname: 'LAST NAME',
        organization: 'ORGANIZATION',
        create: 'CREATE ACCOUNT →',
        dashboard: 'Dashboard',
        dashboard_title: 'Dashboard',
        resumen: 'Summary',
        resumen_title: 'Summary — Word Cloud',
        alerts: 'Alerts',
        alerts_title: 'Alerts Management',
        alerts_sub: 'Configure your personalized information radars',
        new_alert: 'New Alert',
        create_alert: 'CREATE NEW ALERT',
        alert_name: 'ALERT NAME',
        descriptors: 'DESCRIPTORS',
        descriptors_csv: 'DESCRIPTORS (comma-separated)',
        categories: 'CATEGORIES',
        cron: 'PERIODICITY',
        cron_label: 'PERIODICITY (CRON)',
        actions: 'ACTIONS',
        suggest: 'Suggest synonyms (AI)',
        notify_email: 'Notify by email',
        notify_inbox: 'Notify to inbox',
        cancel: 'CANCEL',
        save: 'SAVE',
        save_alert: 'SAVE ALERT',
        sources: 'Sources & RSS',
        sources_title: 'Information Sources',
        sources_tab: 'SOURCES',
        channels_tab: 'RSS CHANNELS',
        add_source: 'Add Source',
        add_source_title: 'ADD SOURCE',
        source_name: 'SOURCE NAME',
        source_url: 'URL',
        notifications: 'Notifications',
        inbox_title: 'Notifications Inbox',
        inbox_sub: 'System messages and alerts',
        search: 'Search',
        search_title: 'News Search & Filter',
        search_sub: 'Filter and search across all captured news',
        search_keyword: 'Keyword',
        filter_category: 'Category',
        filter_from: 'From',
        filter_to: 'To',
        search_btn: 'Search',
        search_news: 'Search news...',
        clear: 'Clear',
        profile: 'Profile',
        profile_title: 'My Profile',
        personal_info: 'PERSONAL INFO',
        edit_profile: 'EDIT PROFILE',
        security: 'SECURITY',
        change_password: 'Change Password',
        roles_perms: 'ROLES & PERMISSIONS',
        logout: 'Logout',
        active_sources: 'ACTIVE SOURCES',
        captured_news: 'CAPTURED NEWS',
        configured_alerts: 'CONFIGURED ALERTS',
        rss_channels: 'RSS CHANNELS',
        capture_evolution: 'Capture Evolution',
        news_per_day: 'News volume per day',
        news_by_category: 'News by Category'
    }
};

function getCurrentLang() {
    return localStorage.getItem('lang') || 'es';
}

function setLang(lang) {
    localStorage.setItem('lang', lang);
    applyTranslations();
}

function toggleLanguage() {
    const newLang = getCurrentLang() === 'es' ? 'en' : 'es';
    setLang(newLang);
}

function t(key) {
    const lang = getCurrentLang();
    return translations[lang][key] || translations.es[key] || key;
}

function applyTranslations() {
    const lang = getCurrentLang();
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) el.textContent = translations[lang][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang][key]) el.setAttribute('placeholder', translations[lang][key]);
    });
    const btn = document.getElementById('lang-btn');
    if (btn) btn.textContent = lang === 'es' ? 'EN' : 'ES';
}

// Apply on load
document.addEventListener('DOMContentLoaded', applyTranslations);
