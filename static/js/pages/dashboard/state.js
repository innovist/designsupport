// Dashboard shared state and helpers
const _t = (key, params) => window.t ? window.t(key, params) : key;

const dashboardState = {
    currentProjectId: null,
    currentSessionId: null,
    currentSessionData: null,
    projects: [],
    sessions: [],
    crawlerList: [],
    crawlerConfig: {},
    youtubeChannels: [],
    imageModelStatus: {
        gpuAvailable: null,
        gpuInfo: null,
        zimageAvailable: false
    },
    reportCache: {
        sessionId: null,
        language: null,
        data: null
    },
    activeTab: 'overview'
};

function getCurrentLanguage() {
    return window.i18n?.currentLanguage || 'ko';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function getTranslatedValue(key, fallback) {
    const value = _t(key);
    return value === key ? fallback : value;
}

function getCrawlerLabel(crawler) {
    return getTranslatedValue(`crawlers.names.${crawler.id}`, crawler.name || crawler.id);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString(window.i18n?.getNumberLocale() || 'ko-KR', { month: 'short', day: 'numeric' });
}

function getStatusText(status) {
    const map = {
        created: _t('status.created'),
        running: _t('status.running'),
        analyzing: _t('status.analyzing'),
        completed: _t('status.completed'),
        failed: _t('status.failed'),
        cancelled: _t('status.cancelled'),
        draft: _t('status.draft'),
        active: _t('status.active')
    };
    return map[status] || _t('status.unknown');
}

function getSelectedCheckboxValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(c => c.value);
}

window.dashboardState = dashboardState;
window.dashboardUtils = {
    _t,
    escapeHtml,
    getCurrentLanguage,
    getTranslatedValue,
    getCrawlerLabel,
    formatDate,
    getStatusText,
    getSelectedCheckboxValues
};
