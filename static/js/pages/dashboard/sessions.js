// Session handlers
(function() {
const sessionState = window.dashboardState;
const {
    _t,
    escapeHtml,
    formatDate,
    getStatusText,
    getSelectedCheckboxValues
} = window.dashboardUtils;
async function loadSessions(projectId) {
    try {
        const res = await fetch(`/api/v1/sessions/?project_id=${projectId}`);
        if (res.ok) {
            sessionState.sessions = await res.json();
            renderSessions();
        }
    } catch (e) {
        console.error('Sessions load error:', e);
    }
}
function renderSessions() {
    const container = document.getElementById('session-list');
    if (!sessionState.sessions.length) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 16px;">
                ${_t('dashboard.empty.sessions')}
            </div>
        `;
        return;
    }
    container.innerHTML = sessionState.sessions.map(s => {
        const statusColor = s.status === 'completed' ? '#10b981' : s.status === 'running' ? '#f59e0b' : '#6b7280';
        return `
        <div class="item-card ${sessionState.currentSessionId === s.id ? 'active' : ''}" onclick="selectSession(${s.id})" style="border-left: 3px solid ${statusColor};">
            <div class="item-title">${escapeHtml(s.session_title || _t('common.noTitle'))}</div>
            <div class="item-meta">${getStatusText(s.status)} | ${formatDate(s.created_at)}</div>
        </div>
    `}).join('');
}
async function selectSession(sessionId) {
    sessionState.currentSessionId = sessionId;
    renderSessions();
    await loadSessionDetails(sessionId);
}
async function loadSessionDetails(sessionId) {
    try {
        const res = await fetch(`/api/v1/sessions/${sessionId}`);
        if (res.ok) {
            const session = await res.json();
            sessionState.currentSessionData = session;
            updateReportPanel(session);
        }
    } catch (e) {
        console.error('Session details error:', e);
    }
}
function updateReportPanel(session) {
    document.getElementById('session-title').textContent = session.session_title || _t('common.noTitle');
    document.getElementById('session-desc').textContent = session.description || _t('dashboard.placeholders.sessionHelp');
    document.getElementById('session-actions').style.display = 'flex';
    document.getElementById('edit-session-btn').style.display = 'inline-block';
    document.getElementById('delete-session-btn').style.display = 'inline-block';
    if (session.status === 'running' || session.status === 'analyzing') {
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('progress-bar').style.width = (session.progress_percent || 0) + '%';
        document.getElementById('progress-percent').textContent = (session.progress_percent || 0) + '%';
        if (session.current_step) {
            document.getElementById('progress-step').textContent = _t(`pipeline.steps.${session.current_step}`);
        } else {
            document.getElementById('progress-step').textContent = _t('dashboard.progress.preparing');
        }
    } else {
        document.getElementById('progress-container').style.display = 'none';
    }
    const runBtn = document.getElementById('run-analysis-btn');
    if (session.status === 'completed') {
        runBtn.textContent = _t('dashboard.actions.reanalyze');
        runBtn.disabled = false;
    } else if (session.status === 'running') {
        runBtn.textContent = _t('dashboard.actions.running');
        runBtn.disabled = true;
    } else {
        runBtn.textContent = _t('dashboard.actions.startAnalysis');
        runBtn.disabled = false;
    }
    document.getElementById('inline-stats').style.display = 'block';
    document.getElementById('stat-crawled-inline').textContent = session.crawled_count || 0;
    document.getElementById('stat-keywords-inline').textContent = session.keyword_count || 0;
    document.getElementById('stat-designs-inline').textContent = session.design_count || 0;
    document.getElementById('stat-models-inline').textContent = session.model_image_count || 0;
    document.getElementById('tabs-section').style.display = 'flex';
    loadTabContents(session);
}
function resetReportPanel() {
    document.getElementById('session-title').textContent = _t('dashboard.placeholders.selectSession');
    document.getElementById('session-desc').textContent = _t('dashboard.placeholders.sessionHelp');
    document.getElementById('session-actions').style.display = 'none';
    document.getElementById('progress-container').style.display = 'none';
    document.getElementById('inline-stats').style.display = 'none';
    document.getElementById('tabs-section').style.display = 'none';
    document.getElementById('edit-session-btn').style.display = 'none';
    document.getElementById('delete-session-btn').style.display = 'none';
}
async function runAnalysis() {
    if (!sessionState.currentSessionId) return;
    const btn = document.getElementById('run-analysis-btn');
    btn.disabled = true;
    btn.textContent = _t('dashboard.actions.starting');
    try {
        const res = await fetch(`/api/v1/sessions/${sessionState.currentSessionId}/run-analysis`, { method: 'POST' });
        if (res.ok) {
            startProgressPolling();
        } else {
            alert(_t('dashboard.messages.runFailed'));
            btn.disabled = false;
            btn.textContent = _t('dashboard.actions.startAnalysis');
        }
    } catch (e) {
        console.error('Run analysis error:', e);
        btn.disabled = false;
        btn.textContent = _t('dashboard.actions.startAnalysis');
    }
}
function startProgressPolling() {
    const interval = setInterval(async () => {
        if (!sessionState.currentSessionId) { clearInterval(interval); return; }
        try {
            const res = await fetch(`/api/v1/sessions/${sessionState.currentSessionId}`);
            if (res.ok) {
                const session = await res.json();
                sessionState.currentSessionData = session;
                updateReportPanel(session);
                if (session.status === 'completed' || session.status === 'failed') {
                    clearInterval(interval);
                }
            }
        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 2000);
}
function showCreateSessionModal() {
    if (!sessionState.currentProjectId) { alert(_t('dashboard.messages.selectProject')); return; }
    document.getElementById('session-modal').style.display = 'flex';
    document.getElementById('session-title-input').focus();
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    const formatDateInput = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    const startDateInput = document.getElementById('crawl-start-date');
    const endDateInput = document.getElementById('crawl-end-date');
    if (startDateInput) startDateInput.value = formatDateInput(oneMonthAgo);
    if (endDateInput) endDateInput.value = formatDateInput(today);
}
function closeSessionModal() {
    document.getElementById('session-modal').style.display = 'none';
    document.getElementById('session-form').reset();
}
async function createSession() {
    const title = document.getElementById('session-title-input').value.trim();
    const desc = document.getElementById('session-desc-input').value.trim();
    if (!title) { alert(_t('newSession.messages.required')); return; }
    const selectedCrawlers = Array.from(document.querySelectorAll('input[name="crawlers"]:checked')).map(c => c.value);
    if (selectedCrawlers.includes('searxng') && !sessionState.crawlerConfig?.searxng_api_url) {
        alert(_t('dashboard.messages.searxngConfigRequired'));
        return;
    }
    const genders = getSelectedCheckboxValues('filter-gender');
    const ages = getSelectedCheckboxValues('filter-age');
    const seasons = getSelectedCheckboxValues('filter-season');
    const categories = getSelectedCheckboxValues('filter-category');
    const youtubeChannelUrls = getSelectedYoutubeChannels();
    const startDate = document.getElementById('crawl-start-date')?.value || null;
    const endDate = document.getElementById('crawl-end-date')?.value || null;
    const maxPostsPerCrawler = parseInt(document.getElementById('max-posts-per-crawler')?.value) || 50;
    const youtubeKeywordCount = parseInt(document.getElementById('youtube-keyword-count')?.value) || 10;
    const youtubeChannelMax = parseInt(document.getElementById('youtube-channel-max')?.value) || 20;
    const youtubeParallel = parseInt(document.getElementById('youtube-parallel')?.value) || 1;
    const youtubeEnableStt = true;
    try {
        const res = await fetch('/api/v1/sessions/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: sessionState.currentProjectId,
                session_title: title,
                description: desc,
                filters: { gender: genders.length > 0 ? genders : null, age: ages.length > 0 ? ages : null, season: seasons.length > 0 ? seasons : null, category: categories.length > 0 ? categories : null },
                crawler_config: { crawlers: selectedCrawlers, youtube_channel_urls: youtubeChannelUrls, start_date: startDate, end_date: endDate, max_items_per_source: maxPostsPerCrawler, youtube_keyword_count: youtubeKeywordCount, youtube_channel_max: youtubeChannelMax, youtube_parallel: youtubeParallel, youtube_enable_stt: youtubeEnableStt },
                auto_start: true,
                generate_images: true,
                generate_blueprints: false
            })
        });
        if (res.ok) {
            const newSession = await res.json();
            closeSessionModal();
            await loadSessions(sessionState.currentProjectId);
            if (newSession && newSession.id) {
                selectSession(newSession.id);
                startProgressPolling();
            }
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.createFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Create session error:', e);
        alert(_t('dashboard.messages.sessionCreateError'));
    }
}
function showEditSessionModal() {
    if (!sessionState.currentSessionId || !sessionState.currentSessionData) return;
    document.getElementById('edit-session-id').value = sessionState.currentSessionData.id;
    document.getElementById('edit-session-title').value = sessionState.currentSessionData.session_title || '';
    document.getElementById('edit-session-desc').value = sessionState.currentSessionData.description || '';
    document.getElementById('edit-session-modal').style.display = 'flex';
    document.getElementById('edit-session-title').focus();
}
function closeEditSessionModal() {
    document.getElementById('edit-session-modal').style.display = 'none';
    document.getElementById('edit-session-form').reset();
}
async function updateSession() {
    const sessionId = document.getElementById('edit-session-id').value;
    const title = document.getElementById('edit-session-title').value.trim();
    const desc = document.getElementById('edit-session-desc').value.trim();
    if (!title) { alert(_t('newSession.messages.required')); return; }
    try {
        const res = await fetch(`/api/v1/sessions/${sessionId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_title: title, description: desc })
        });
        if (res.ok) {
            closeEditSessionModal();
            await loadSessions(sessionState.currentProjectId);
            await loadSessionDetails(parseInt(sessionId, 10));
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.updateFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Update session error:', e);
        alert(_t('dashboard.messages.sessionUpdateError'));
    }
}
async function confirmDeleteSession() {
    if (!sessionState.currentSessionId || !sessionState.currentSessionData) return;
    const sessionName = sessionState.currentSessionData.session_title || '';
    if (!confirm(_t('dashboard.messages.confirmDeleteSession', { name: sessionName }))) return;
    try {
        const res = await fetch(`/api/v1/sessions/${sessionState.currentSessionId}`, { method: 'DELETE' });
        if (res.ok) {
            sessionState.currentSessionId = null;
            sessionState.currentSessionData = null;
            await loadSessions(sessionState.currentProjectId);
            resetReportPanel();
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.deleteFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Delete session error:', e);
        alert(_t('dashboard.messages.sessionDeleteError'));
    }
}
window.loadSessions = loadSessions;
window.renderSessions = renderSessions;
window.selectSession = selectSession;
window.loadSessionDetails = loadSessionDetails;
window.updateReportPanel = updateReportPanel;
window.resetReportPanel = resetReportPanel;
window.runAnalysis = runAnalysis;
window.startProgressPolling = startProgressPolling;
window.showCreateSessionModal = showCreateSessionModal;
window.closeSessionModal = closeSessionModal;
window.createSession = createSession;
window.showEditSessionModal = showEditSessionModal;
window.closeEditSessionModal = closeEditSessionModal;
window.updateSession = updateSession;
window.confirmDeleteSession = confirmDeleteSession;
})();
