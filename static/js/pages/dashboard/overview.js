// @MX:NOTE: [AUTO] Overview tab renderer displaying session summary, keywords, metrics, and crawl logs
// @MX:REASON: Provides real-time pipeline progress visualization and terminal-style log streaming
// Overview tab handlers
(function() {
const {
    _t,
    escapeHtml,
    formatDate,
    getStatusText
} = window.dashboardUtils;

function formatFilter(value, prefix) {
    if (!value) return _t('common.all');
    const values = Array.isArray(value) ? value : [value];
    return values.map(item => _t(`${prefix}.${item}`)).join(', ');
}

function formatLogTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleTimeString(window.i18n?.getNumberLocale() || 'ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function getLogStepLabel(step) {
    if (!step) return '';
    const key = `pipeline.steps.${step}`;
    const label = _t(key);
    return label === key ? step : label;
}

async function loadOverviewLogs(sessionId) {
    const container = document.getElementById('overview-crawl-logs');
    if (!container || !sessionId) return;
    container.innerHTML = `<div class="terminal-line muted">${_t('common.loading')}</div>`;
    try {
        const res = await fetch(`/api/v1/sessions/${sessionId}/logs?limit=200`);
        if (!res.ok) throw new Error('logs fetch failed');
        const data = await res.json();
        const logs = data.logs || [];
        if (!logs.length) {
            container.innerHTML = `<div class="terminal-line muted">${_t('dashboard.overview.logsEmpty')}</div>`;
            return;
        }
        container.innerHTML = logs.map(log => {
            const timeText = escapeHtml(formatLogTime(log.timestamp));
            const stepText = escapeHtml(getLogStepLabel(log.step));
            const messageText = escapeHtml(log.message || '');
            return `
                <div class="terminal-line">
                    <span class="terminal-time">${timeText}</span>
                    <span class="terminal-step">${stepText}</span>
                    <span class="terminal-msg">${messageText}</span>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Overview logs error:', error);
        container.innerHTML = `<div class="terminal-line error">${_t('dashboard.overview.logsLoadFailed')}</div>`;
    }
}

function renderOverview(session) {
    const filters = session.filters || {};
    const gender = formatFilter(filters.gender, 'filters.gender.options');
    const season = formatFilter(filters.season, 'filters.season.options');

    const extractedKeywords = Array.isArray(session.extracted_keywords) ? session.extracted_keywords : [];
    const userKeywords = Array.isArray(session.user_keywords) ? session.user_keywords : [];
    const crawlKeywords = extractedKeywords.length ? extractedKeywords : userKeywords;
    const keywordChips = crawlKeywords.length
        ? crawlKeywords.map(keyword => `<span class="keyword-chip">${escapeHtml(keyword)}</span>`).join('')
        : `<span style="color: var(--text-muted); font-size: 12px;">${_t('dashboard.overview.keywordsEmpty')}</span>`;

    const collected = Number(session.crawl_collected_items || 0);
    const expected = Number(session.crawl_expected_items || 0);
    const completedKeywords = Number(session.crawl_completed_keywords || 0);
    const totalKeywords = Number(session.crawl_total_keywords || 0);
    const collectedText = expected > 0 ? `${collected} / ${expected}` : _t('ui.unknown');
    const keywordProgressText = totalKeywords > 0 ? `${completedKeywords} / ${totalKeywords}` : _t('ui.unknown');
    const errorBlock = session.status === 'failed' && session.error_message
        ? `<div class="overview-error">${_t('dashboard.overview.errorTitle')}: ${escapeHtml(session.error_message)}</div>`
        : '';

    document.getElementById('overview-content').innerHTML = `
        <div style="padding: 16px; display: grid; gap: 16px;">
            <div>
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">${_t('dashboard.summary.title')}</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span style="color: var(--text-muted);">${_t('dashboard.summary.status')}:</span> <span style="font-weight: 500;">${getStatusText(session.status)}</span></div>
                    <div><span style="color: var(--text-muted);">${_t('dashboard.summary.createdAt')}:</span> <span>${formatDate(session.created_at)}</span></div>
                    <div><span style="color: var(--text-muted);">${_t('dashboard.summary.gender')}:</span> <span>${gender}</span></div>
                    <div><span style="color: var(--text-muted);">${_t('dashboard.summary.season')}:</span> <span>${season}</span></div>
                </div>
                ${session.description ? `<p style="margin-top: 12px; color: var(--text-secondary);">${escapeHtml(session.description)}</p>` : ''}
                ${errorBlock}
            </div>
            <div>
                <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">${_t('dashboard.overview.keywordsTitle')}</h4>
                <div class="keyword-chip-group">${keywordChips}</div>
            </div>
            <div class="overview-metrics">
                <div class="overview-metric">
                    <div class="overview-metric-label">${_t('dashboard.overview.crawlProgress')}</div>
                    <div class="overview-metric-value">${escapeHtml(collectedText)}</div>
                </div>
                <div class="overview-metric">
                    <div class="overview-metric-label">${_t('dashboard.overview.keywordProgress')}</div>
                    <div class="overview-metric-value">${escapeHtml(keywordProgressText)}</div>
                </div>
            </div>
            <div>
                <div class="overview-section-header">
                    <span>${_t('dashboard.overview.logsTitle')}</span>
                    <span class="overview-section-meta">${_t('dashboard.overview.logsHint')}</span>
                </div>
                <div id="overview-crawl-logs" class="terminal-log"></div>
            </div>
        </div>
    `;
    loadOverviewLogs(session.id);
}

window.renderOverview = renderOverview;
window.loadOverviewLogs = loadOverviewLogs;
})();
