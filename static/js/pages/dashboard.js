// @MX:WARN: [AUTO] File size exceeds 500 lines (844 lines total) - consider splitting into modules
// @MX:REASON: Large monolithic file reduces maintainability and makes testing difficult
// Dashboard JavaScript for Fashion AI Generation System
// Use _t to avoid conflict with i18n.js global t
const _t = (key, params) => window.t ? window.t(key, params) : key;

let currentProjectId = null;
let currentSessionId = null;
let currentSessionData = null;
let projects = [];
let sessions = [];
let crawlerList = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabHandlers();
    setupFormHandlers();

    // Wait for i18n to be ready before loading data
    if (window.i18n && window.i18n.ready) {
        loadProjects();
        loadCrawlerList();
        loadCrawlerSummary();
        loadYoutubeChannels();
    } else {
        window.addEventListener('i18nReady', () => {
            loadProjects();
            loadCrawlerList();
            loadCrawlerSummary();
            loadYoutubeChannels();
        }, { once: true });
    }
});

function setupTabHandlers() {
    document.querySelectorAll('.report-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.report-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
        });
    });
}

function setupFormHandlers() {
    document.getElementById('project-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createProject();
    });
    document.getElementById('session-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createSession();
    });
    document.getElementById('edit-project-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateProject();
    });
    document.getElementById('edit-session-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateSession();
    });
}

async function loadProjects() {
    try {
        const res = await fetch('/api/v1/projects/');
        if (res.ok) {
            projects = await res.json();
            renderProjects();
        }
    } catch (e) {
        console.error('Projects load error:', e);
    }
}

function renderProjects() {
    const select = document.getElementById('project-select');
    // Keep first option (placeholder)
    const placeholder = `<option value="">${_t('dashboard.placeholders.selectProject')}</option>`;
    if (!projects.length) {
        select.innerHTML = placeholder;
        return;
    }
    select.innerHTML = placeholder + projects.map(p => `
        <option value="${p.id}" ${currentProjectId === p.id ? 'selected' : ''}>
            ${escapeHtml(p.title || p.name || _t('common.noTitle'))} (${p.session_count || 0})
        </option>
    `).join('');
}

function onProjectSelect(value) {
    if (value) {
        selectProject(value);
        // Show edit/delete buttons
        document.getElementById('edit-project-btn').style.display = 'block';
        document.getElementById('delete-project-btn').style.display = 'block';
    } else {
        currentProjectId = null;
        currentSessionId = null;
        document.getElementById('add-session-btn').disabled = true;
        // Hide edit/delete buttons
        document.getElementById('edit-project-btn').style.display = 'none';
        document.getElementById('delete-project-btn').style.display = 'none';
        document.getElementById('session-list').innerHTML = `
            <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 16px;">
                ${_t('dashboard.placeholders.selectProject')}
            </div>
        `;
        resetReportPanel();
    }
}

async function selectProject(projectId) {
    currentProjectId = projectId;
    currentSessionId = null;
    currentSessionData = null;
    renderProjects();
    document.getElementById('add-session-btn').disabled = false;
    await loadSessions(projectId);
    resetReportPanel();
}

async function loadSessions(projectId) {
    try {
        const res = await fetch(`/api/v1/sessions/?project_id=${projectId}`);
        if (res.ok) {
            sessions = await res.json();
            renderSessions();
        }
    } catch (e) {
        console.error('Sessions load error:', e);
    }
}

function renderSessions() {
    const container = document.getElementById('session-list');
    if (!sessions.length) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 16px;">
                ${_t('dashboard.empty.sessions')}
            </div>
        `;
        return;
    }
    container.innerHTML = sessions.map(s => {
        const statusColor = s.status === 'completed' ? '#10b981' : s.status === 'running' ? '#f59e0b' : '#6b7280';
        return `
        <div class="item-card ${currentSessionId === s.id ? 'active' : ''}" onclick="selectSession('${s.id}')" style="border-left: 3px solid ${statusColor};">
            <div class="item-title">${escapeHtml(s.session_title || _t('common.noTitle'))}</div>
            <div class="item-meta">${getStatusText(s.status)} | ${formatDate(s.created_at)}</div>
        </div>
    `}).join('');
}

async function selectSession(sessionId) {
    currentSessionId = sessionId;
    renderSessions();
    await loadSessionDetails(sessionId);
}

async function loadSessionDetails(sessionId) {
    try {
        const res = await fetch(`/api/v1/sessions/${sessionId}`);
        if (res.ok) {
            const session = await res.json();
            currentSessionData = session;
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

    // 세션 수정/삭제 버튼 표시
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

    // 인라인 통계 표시
    document.getElementById('inline-stats').style.display = 'block';
    document.getElementById('stat-crawled-inline').textContent = session.crawled_count || 0;
    document.getElementById('stat-keywords-inline').textContent = session.keyword_count || 0;
    document.getElementById('stat-designs-inline').textContent = session.design_count || 0;
    document.getElementById('stat-models-inline').textContent = session.model_image_count || 0;

    document.getElementById('tabs-section').style.display = 'flex';

    loadTabContents(session);
}

function loadTabContents(session) {
    const filters = session.filters || {};
    const gender = filters.gender ? _t(`filters.gender.options.${filters.gender}`) : _t('common.all');
    const season = filters.season ? _t(`filters.season.options.${filters.season}`) : _t('common.all');

    document.getElementById('overview-content').innerHTML = `
        <div style="padding: 16px;">
            <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">${_t('dashboard.summary.title')}</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div><span style="color: var(--text-muted);">${_t('dashboard.summary.status')}:</span> <span style="font-weight: 500;">${getStatusText(session.status)}</span></div>
                <div><span style="color: var(--text-muted);">${_t('dashboard.summary.createdAt')}:</span> <span>${formatDate(session.created_at)}</span></div>
                <div><span style="color: var(--text-muted);">${_t('dashboard.summary.gender')}:</span> <span>${gender}</span></div>
                <div><span style="color: var(--text-muted);">${_t('dashboard.summary.season')}:</span> <span>${season}</span></div>
            </div>
            ${session.description ? `<p style="margin-top: 16px; color: var(--text-secondary);">${escapeHtml(session.description)}</p>` : ''}
        </div>
    `;
}

function resetReportPanel() {
    document.getElementById('session-title').textContent = _t('dashboard.placeholders.selectSession');
    document.getElementById('session-desc').textContent = _t('dashboard.placeholders.sessionHelp');
    document.getElementById('session-actions').style.display = 'none';
    document.getElementById('progress-container').style.display = 'none';
    document.getElementById('inline-stats').style.display = 'none';
    document.getElementById('tabs-section').style.display = 'none';

    // 세션 수정/삭제 버튼 숨김
    document.getElementById('edit-session-btn').style.display = 'none';
    document.getElementById('delete-session-btn').style.display = 'none';
}

async function runAnalysis() {
    if (!currentSessionId) return;
    const btn = document.getElementById('run-analysis-btn');
    btn.disabled = true;
    btn.textContent = _t('dashboard.actions.starting');

    try {
        const res = await fetch(`/api/v1/sessions/${currentSessionId}/run-analysis`, { method: 'POST' });
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
        if (!currentSessionId) { clearInterval(interval); return; }
        try {
            const res = await fetch(`/api/v1/sessions/${currentSessionId}`);
            if (res.ok) {
                const session = await res.json();
                currentSessionData = session;
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

async function loadCrawlerList() {
    try {
        const res = await fetch('/api/v1/crawlers/list');
        if (res.ok) {
            const data = await res.json();
            crawlerList = [];
            if (data.categorized) {
                Object.values(data.categorized).forEach(cat => {
                    crawlerList.push(...cat.crawlers);
                });
            }
            renderCrawlerCheckboxes();
        }
    } catch (e) {
        console.error('Crawler list error:', e);
    }
}

function renderCrawlerCheckboxes() {
    const container = document.getElementById('crawler-checkboxes');
    container.innerHTML = crawlerList.map(c => `
        <label style="display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer;">
            <input type="checkbox" name="crawlers" value="${c.id}" ${c.enabled ? 'checked' : ''} onchange="onCrawlerChange()">
            ${escapeHtml(getCrawlerLabel(c))}
        </label>
    `).join('');
}

async function loadCrawlerSummary() {
    try {
        const res = await fetch('/api/v1/crawlers/list');
        if (res.ok) {
            const data = await res.json();
            const total = data.counts?.total || 0;
            const enabled = data.counts?.enabled || 0;
            document.getElementById('crawler-summary').innerHTML = `
                <span style="font-size: 11px; color: var(--success);">${_t('dashboard.crawlers.active', { count: enabled })}</span>
                <span style="font-size: 11px; color: var(--text-muted);">${_t('dashboard.crawlers.total', { count: total })}</span>
            `;
        }
    } catch (e) {
        console.error('Crawler summary error:', e);
    }
}

function showCreateProjectModal() {
    document.getElementById('project-modal').style.display = 'flex';
    document.getElementById('project-title').focus();
}

function closeProjectModal() {
    document.getElementById('project-modal').style.display = 'none';
    document.getElementById('project-form').reset();
}

function showCreateSessionModal() {
    if (!currentProjectId) { alert(_t('dashboard.messages.selectProject')); return; }
    document.getElementById('session-modal').style.display = 'flex';
    document.getElementById('session-title-input').focus();

    // 기본 날짜 설정 (오늘부터 1달 전까지)
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);

    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const startDateInput = document.getElementById('crawl-start-date');
    const endDateInput = document.getElementById('crawl-end-date');
    if (startDateInput) startDateInput.value = formatDate(oneMonthAgo);
    if (endDateInput) endDateInput.value = formatDate(today);
}

function closeSessionModal() {
    document.getElementById('session-modal').style.display = 'none';
    document.getElementById('session-form').reset();
}

// 프로젝트 수정 모달
function showEditProjectModal() {
    if (!currentProjectId) return;
    const project = projects.find(p => p.id === currentProjectId);
    if (!project) return;

    document.getElementById('edit-project-id').value = project.id;
    document.getElementById('edit-project-title').value = project.title || project.name || '';
    document.getElementById('edit-project-desc').value = project.description || '';
    document.getElementById('edit-project-modal').style.display = 'flex';
    document.getElementById('edit-project-title').focus();
}

function closeEditProjectModal() {
    document.getElementById('edit-project-modal').style.display = 'none';
    document.getElementById('edit-project-form').reset();
}

async function updateProject() {
    const projectId = document.getElementById('edit-project-id').value;
    const title = document.getElementById('edit-project-title').value.trim();
    const desc = document.getElementById('edit-project-desc').value.trim();

    if (!title) { alert(_t('dashboard.messages.projectNameRequired')); return; }

    try {
        const res = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title, description: desc })
        });
        if (res.ok) {
            closeEditProjectModal();
            await loadProjects();
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.updateFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Update project error:', e);
        alert(_t('dashboard.messages.projectUpdateError'));
    }
}

async function confirmDeleteProject() {
    if (!currentProjectId) return;
    const project = projects.find(p => p.id === currentProjectId);
    const projectName = project ? (project.title || project.name) : '';

    if (!confirm(_t('dashboard.messages.confirmDeleteProject', { name: projectName }))) return;

    try {
        const res = await fetch(`/api/v1/projects/${currentProjectId}`, { method: 'DELETE' });
        if (res.ok) {
            currentProjectId = null;
            currentSessionId = null;
            document.getElementById('edit-project-btn').style.display = 'none';
            document.getElementById('delete-project-btn').style.display = 'none';
            await loadProjects();
            document.getElementById('session-list').innerHTML = `
                <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 16px;">
                    ${_t('dashboard.placeholders.selectProject')}
                </div>
            `;
            resetReportPanel();
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.deleteFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Delete project error:', e);
        alert(_t('dashboard.messages.projectDeleteError'));
    }
}

// 세션 수정 모달
function showEditSessionModal() {
    if (!currentSessionId || !currentSessionData) return;

    document.getElementById('edit-session-id').value = currentSessionData.id;
    document.getElementById('edit-session-title').value = currentSessionData.session_title || '';
    document.getElementById('edit-session-desc').value = currentSessionData.description || '';
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
            await loadSessions(currentProjectId);
            await loadSessionDetails(sessionId);
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
    if (!currentSessionId || !currentSessionData) return;
    const sessionName = currentSessionData.session_title || '';

    if (!confirm(_t('dashboard.messages.confirmDeleteSession', { name: sessionName }))) return;

    try {
        const res = await fetch(`/api/v1/sessions/${currentSessionId}`, { method: 'DELETE' });
        if (res.ok) {
            currentSessionId = null;
            currentSessionData = null;
            await loadSessions(currentProjectId);
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

async function createProject() {
    const title = document.getElementById('project-title').value.trim();
    const desc = document.getElementById('project-desc').value.trim();
    if (!title) { alert(_t('dashboard.messages.projectNameRequired')); return; }

    try {
        const res = await fetch('/api/v1/projects/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title, prompt: title, description: desc })
        });
        if (res.ok) {
            closeProjectModal();
            await loadProjects();
        } else {
            const err = await res.json();
            alert(_t('dashboard.messages.createFailed', { error: err.detail || _t('common.unknownError') }));
        }
    } catch (e) {
        console.error('Create project error:', e);
        alert(_t('dashboard.messages.projectCreateError'));
    }
}

function getSelectedCheckboxValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(c => c.value);
}

// @MX:WARN: [AUTO] Complex async function with 8+ branches and multiple API calls without error boundary
// @MX:REASON: Function handles session creation, file upload, and analysis triggering - failure in later steps can leave inconsistent state
async function createSession() {
    const title = document.getElementById('session-title-input').value.trim();
    const desc = document.getElementById('session-desc-input').value.trim();
    if (!title) { alert(_t('newSession.messages.required')); return; }

    const selectedCrawlers = Array.from(document.querySelectorAll('input[name="crawlers"]:checked')).map(c => c.value);

    // Get multi-select filter values
    const genders = getSelectedCheckboxValues('filter-gender');
    const seasons = getSelectedCheckboxValues('filter-season');
    const categories = getSelectedCheckboxValues('filter-category');

    // 유튜브 채널 URL 가져오기
    const youtubeChannelUrls = getSelectedYoutubeChannels();

    // 수집 기간 설정
    const startDate = document.getElementById('crawl-start-date')?.value || null;
    const endDate = document.getElementById('crawl-end-date')?.value || null;
    const maxPostsPerCrawler = parseInt(document.getElementById('max-posts-per-crawler')?.value) || 50;

    // 유튜브 설정
    const youtubeKeywordCount = parseInt(document.getElementById('youtube-keyword-count')?.value) || 10;
    const youtubeChannelMax = parseInt(document.getElementById('youtube-channel-max')?.value) || 20;
    const youtubeParallel = parseInt(document.getElementById('youtube-parallel')?.value) || 1;

    try {
        const res = await fetch('/api/v1/sessions/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                session_title: title,
                description: desc,
                filters: {
                    gender: genders.length > 0 ? genders : null,
                    season: seasons.length > 0 ? seasons : null,
                    category: categories.length > 0 ? categories : null
                },
                crawler_config: {
                    crawlers: selectedCrawlers,
                    youtube_channel_urls: youtubeChannelUrls,
                    start_date: startDate,
                    end_date: endDate,
                    max_items_per_source: maxPostsPerCrawler,
                    youtube_keyword_count: youtubeKeywordCount,
                    youtube_channel_max: youtubeChannelMax,
                    youtube_parallel: youtubeParallel
                },
                auto_start: true,
                generate_images: true,
                generate_blueprints: false
            })
        });
        if (res.ok) {
            // Get new session data first
            const newSession = await res.json();
            closeSessionModal();
            await loadSessions(currentProjectId);
            // Auto-select the newly created session and start polling
            if (newSession && newSession.id) {
                selectSession(newSession.id);
                // Start progress polling since auto_start is true
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

// Modal close on background click
document.getElementById('project-modal').addEventListener('click', (e) => {
    if (e.target.id === 'project-modal') closeProjectModal();
});
document.getElementById('session-modal').addEventListener('click', (e) => {
    if (e.target.id === 'session-modal') closeSessionModal();
});
document.getElementById('edit-project-modal').addEventListener('click', (e) => {
    if (e.target.id === 'edit-project-modal') closeEditProjectModal();
});
document.getElementById('edit-session-modal').addEventListener('click', (e) => {
    if (e.target.id === 'edit-session-modal') closeEditSessionModal();
});

// Language change handler
window.addEventListener('languageChanged', () => {
    renderProjects();
    renderSessions();
    loadCrawlerSummary();
    if (crawlerList.length) {
        renderCrawlerCheckboxes();
    }
    renderYoutubeChannels();
    if (currentSessionData) {
        updateReportPanel(currentSessionData);
    } else {
        resetReportPanel();
    }
});

// ========== 크롤러 전체선택/전체해제 ==========
function selectAllCrawlers() {
    document.querySelectorAll('input[name="crawlers"]').forEach(cb => cb.checked = true);
}

function deselectAllCrawlers() {
    document.querySelectorAll('input[name="crawlers"]').forEach(cb => cb.checked = false);
}

// ========== 유튜브 채널 관리 ==========
let youtubeChannels = [];

async function loadYoutubeChannels() {
    try {
        const res = await fetch('/api/v1/youtube-channels/');
        if (!res.ok) throw new Error(_t('youtube.loadFailed'));
        youtubeChannels = await res.json();
        youtubeChannels.forEach(ch => ch.selected = ch.is_active);
        renderYoutubeChannels();
    } catch (err) {
        console.error('유튜브 채널 로드 오류:', err);
        document.getElementById('youtube-channels-list').innerHTML =
            `<span style="color: var(--text-muted); font-size: 11px; grid-column: 1 / -1; text-align: center;">${_t('youtube.empty')}</span>`;
    }
}

function renderYoutubeChannels() {
    const container = document.getElementById('youtube-channels-list');
    const isYoutubeEnabled = isYoutubeCrawlerSelected();

    if (youtubeChannels.length === 0) {
        container.innerHTML = `<span style="color: var(--text-muted); font-size: 11px; grid-column: 1 / -1; text-align: center;">${_t('youtube.empty')}</span>`;
        return;
    }

    container.innerHTML = youtubeChannels.map(ch => `
        <div style="display: flex; align-items: center; gap: 4px; padding: 4px 6px; background: ${isYoutubeEnabled ? '#f5f5f5' : '#e5e5e5'}; border-radius: 4px; opacity: ${isYoutubeEnabled ? '1' : '0.5'};">
            <input type="checkbox" ${ch.selected ? 'checked' : ''} ${isYoutubeEnabled ? '' : 'disabled'} onchange="toggleYoutubeChannel(${ch.id})" style="width: 12px; height: 12px; margin: 0;">
            <span style="flex: 1; font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${ch.channel_url || ch.channel_id}">${ch.channel_name || ch.channel_handle || ch.channel_id}</span>
            <button type="button" onclick="removeYoutubeChannel(${ch.id})" aria-label="${_t('common.delete')}" style="padding: 0 3px; font-size: 10px; background: #fee2e2; color: #b91c1c; border: none; border-radius: 2px; cursor: pointer; line-height: 1;">×</button>
        </div>
    `).join('');
}

function isYoutubeCrawlerSelected() {
    const ytCrawler = document.querySelector('input[name="crawlers"][value="youtube"]');
    return ytCrawler && ytCrawler.checked;
}

function toggleYoutubeChannel(channelId) {
    const ch = youtubeChannels.find(c => c.id === channelId);
    if (ch) ch.selected = !ch.selected;
}

async function addYoutubeChannel() {
    const url = prompt(_t('youtube.prompt'));
    if (!url) return;

    if (!url.includes('youtube.com/') && !url.includes('youtu.be/')) {
        alert(_t('youtube.invalidUrl'));
        return;
    }

    let channelId = '', channelHandle = '', channelName = '';

    if (url.includes('@')) {
        channelHandle = '@' + url.split('@')[1].split('/')[0].split('?')[0];
        channelName = channelHandle;
        channelId = channelHandle;
    } else if (url.includes('/channel/')) {
        channelId = url.split('/channel/')[1].split('/')[0].split('?')[0];
        channelName = channelId;
    } else if (url.includes('/c/')) {
        channelName = url.split('/c/')[1].split('/')[0].split('?')[0];
        channelId = channelName;
    } else {
        alert(_t('youtube.invalidFormat'));
        return;
    }

    if (youtubeChannels.some(ch => ch.channel_id === channelId || ch.channel_url === url)) {
        alert(_t('youtube.duplicate'));
        return;
    }

    try {
        const res = await fetch('/api/v1/youtube-channels/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel_id: channelId,
                channel_handle: channelHandle || null,
                channel_name: channelName,
                channel_url: url,
                category: '패션'
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || _t('common.unknownError'));
        }

        await loadYoutubeChannels();
        alert(_t('youtube.added', { name: channelName }));
    } catch (err) {
        console.error('채널 등록 오류:', err);
        alert(_t('youtube.addFailed', { error: err.message || _t('common.unknownError') }));
    }
}

async function removeYoutubeChannel(channelId) {
    if (!confirm(_t('youtube.deleteConfirm'))) return;

    try {
        const res = await fetch(`/api/v1/youtube-channels/${channelId}`, { method: 'DELETE' });
        if (!res.ok) {
            let detail = _t('common.unknownError');
            try {
                const err = await res.json();
                detail = err.detail || detail;
            } catch (error) {
                console.error('Delete response parse error:', error);
            }
            throw new Error(detail);
        }
        await loadYoutubeChannels();
    } catch (err) {
        console.error('채널 삭제 오류:', err);
        alert(_t('youtube.deleteFailed', { error: err.message || _t('common.unknownError') }));
    }
}

function getSelectedYoutubeChannels() {
    return youtubeChannels.filter(ch => ch.selected).map(ch => ch.channel_url || ch.channel_id);
}

// 크롤러 체크박스 변경 시 유튜브 채널 상태 업데이트
function onCrawlerChange() {
    renderYoutubeChannels();
}

// Expose functions to global scope for onclick handlers
window.showCreateProjectModal = showCreateProjectModal;
window.closeProjectModal = closeProjectModal;
window.showCreateSessionModal = showCreateSessionModal;
window.closeSessionModal = closeSessionModal;
window.selectProject = selectProject;
window.onProjectSelect = onProjectSelect;
window.selectSession = selectSession;
window.runAnalysis = runAnalysis;
window.showEditProjectModal = showEditProjectModal;
window.closeEditProjectModal = closeEditProjectModal;
window.confirmDeleteProject = confirmDeleteProject;
window.showEditSessionModal = showEditSessionModal;
window.closeEditSessionModal = closeEditSessionModal;
window.confirmDeleteSession = confirmDeleteSession;
window.selectAllCrawlers = selectAllCrawlers;
window.deselectAllCrawlers = deselectAllCrawlers;
window.addYoutubeChannel = addYoutubeChannel;
window.removeYoutubeChannel = removeYoutubeChannel;
window.toggleYoutubeChannel = toggleYoutubeChannel;
window.onCrawlerChange = onCrawlerChange;
