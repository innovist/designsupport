// Dashboard initialization
const initState = window.dashboardState;

function setupFormHandlers() {
    document.getElementById('project-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        await window.createProject();
    });
    document.getElementById('session-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        await window.createSession();
    });
    document.getElementById('edit-project-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        await window.updateProject();
    });
    document.getElementById('edit-session-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        await window.updateSession();
    });
}

function bindModalClose(modalId, closeFn) {
    const modal = document.getElementById(modalId);
    modal.addEventListener('click', (event) => {
        if (event.target.id === modalId) {
            closeFn();
        }
    });
}

function setupModalCloseHandlers() {
    bindModalClose('project-modal', window.closeProjectModal);
    bindModalClose('session-modal', window.closeSessionModal);
    bindModalClose('edit-project-modal', window.closeEditProjectModal);
    bindModalClose('edit-session-modal', window.closeEditSessionModal);
}

function loadInitialData() {
    window.loadProjects();
    window.loadCrawlerList();
    window.loadCrawlerSummary();
    window.loadYoutubeChannels();
    window.loadImageModelStatus();
}

function handleLanguageChange() {
    window.renderProjects();
    window.renderSessions();
    window.loadCrawlerSummary();
    if (initState.crawlerList.length) {
        window.renderCrawlerCheckboxes();
    }
    window.renderYoutubeChannels();
    window.updateImageModelSelectors();

    if (initState.currentSessionData) {
        window.updateReportPanel(initState.currentSessionData);
    } else {
        window.resetReportPanel();
    }
    window.refreshReportOnLanguageChange();
}

function initDashboard() {
    window.setupTabHandlers();
    setupFormHandlers();
    setupModalCloseHandlers();
    loadInitialData();
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.i18n && window.i18n.ready) {
        initDashboard();
    } else {
        window.addEventListener('i18nReady', () => {
            initDashboard();
        }, { once: true });
    }
});

window.addEventListener('languageChanged', handleLanguageChange);
