// @MX:NOTE: [AUTO] Report display module handling analysis results, design images, and blueprint rendering
// @MX:REASON: Manages tab switching, image galleries, and multi-language report caching
// Report and tab handlers
(function() {
const reportState = window.dashboardState;
const {
    _t,
    escapeHtml,
    getCurrentLanguage,
    formatDate
} = window.dashboardUtils;
let currentImage = null;

function setupTabHandlers() {
    document.querySelectorAll('.report-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.report-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            reportState.activeTab = tab.dataset.tab;
            if (reportState.activeTab === 'analysis') {
                loadReportForCurrentSession(false);
            }
        });
    });
}

function loadTabContents(session) {
    if (!session) return;
    if (window.renderOverview) {
        window.renderOverview(session);
    }
    renderDataTab(session);
    renderImageTabs(session);
    if (reportState.activeTab === 'analysis') {
        loadReportForCurrentSession(false);
    }
}


function renderDataTab(session) {
    const dataContainer = document.getElementById('data-content');
    const results = session.pipeline_results || {};
    const crawled = results.crawled_data || [];
    if (!crawled.length) {
        dataContainer.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 32px;">${_t('dashboard.empty.data')}</p>`;
        return;
    }
    const items = crawled.slice(0, 8).map(item => `
        <div style="padding: 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-secondary);">
            <div style="font-size: 12px; font-weight: 600; margin-bottom: 4px;">${escapeHtml(item.title || item.source || _t('common.noTitle'))}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml((item.summary || item.content || '').slice(0, 120))}</div>
        </div>
    `).join('');
    dataContainer.innerHTML = `<div style="display: grid; gap: 10px; padding: 16px;">${items}</div>`;
}

function renderImageTabs(session) {
    const results = session.pipeline_results || {};
    const images = results.generated_images || [];
    const blueprints = results.blueprints || [];

    const designContainer = document.getElementById('design-content');
    const modelContainer = document.getElementById('model-content');
    const blueprintContainer = document.getElementById('blueprint-content');

    const designs = images.filter(img => img.type === 'design');
    const models = images.filter(img => img.type === 'model');
    const projectName = getCurrentProjectName();

    renderImageGrid(designContainer, designs, 'design', session, projectName);
    renderImageGrid(modelContainer, models, 'model', session, projectName);
    renderImageGrid(blueprintContainer, blueprints, 'blueprint', session, projectName);
}

function renderImageGrid(container, items, type, session, projectName) {
    if (!container) return;
    if (!items.length) {
        let key = 'dashboard.empty.designImages';
        if (type === 'model') {
            key = 'dashboard.empty.modelImages';
        } else if (type === 'blueprint') {
            key = 'dashboard.empty.blueprints';
        }
        container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 32px;">${_t(key)}</p>`;
        return;
    }
    const enrichedItems = items.map(item => ({
        ...item,
        session_title: session?.session_title,
        project_name: projectName || '-'
    }));
    container.innerHTML = enrichedItems.map(item => `
        <div class="image-card">
            <img src="${item.url || `data:image/jpeg;base64,${item.image_base64}`}" alt="${escapeHtml(item.title || '')}" style="width: 100%; height: 100%; object-fit: cover;">
            <div class="image-info">
                <div class="image-title">${escapeHtml(item.title || '')}</div>
                <div class="image-meta">${escapeHtml(item.model_used || getTypeLabel(item.type))}</div>
            </div>
        </div>
    `).join('');
    container.querySelectorAll('.image-card').forEach((card, index) => {
        card.addEventListener('click', () => openImageModal(enrichedItems[index]));
    });
}

function resetReportCache() {
    reportState.reportCache = {
        sessionId: null,
        language: null,
        data: null
    };
}

function setReportMessage(messageKey) {
    const container = document.getElementById('analysis-content');
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 32px;">${_t(messageKey)}</p>`;
}

function getLanguageLabel(language) {
    if (!language) return '';
    const map = {
        'ko': 'common.languages.ko',
        'en': 'common.languages.en',
        'zh-CN': 'common.languages.zhCn',
        'zh-TW': 'common.languages.zhTw'
    };
    const key = map[language];
    return key ? _t(key) : language;
}

function renderReport(report) {
    const sections = [
        { key: 'executive_summary', label: _t('dashboard.report.sections.executiveSummary') },
        { key: 'target_audience', label: _t('dashboard.report.sections.targetAudience') },
        { key: 'research_scope', label: _t('dashboard.report.sections.researchScope') },
        { key: 'market_analysis', label: _t('dashboard.report.sections.marketAnalysis') },
        { key: 'trend_analysis', label: _t('dashboard.report.sections.trendAnalysis') },
        { key: 'competitor_analysis', label: _t('dashboard.report.sections.competitorAnalysis') },
        { key: 'design_proposals', label: _t('dashboard.report.sections.designProposals') },
        { key: 'recommendations', label: _t('dashboard.report.sections.recommendations') },
        { key: 'conclusion', label: _t('dashboard.report.sections.conclusion') }
    ];

    const blocks = sections.map(section => {
        const value = report[section.key];
        if (!value) return '';
        const content = section.key === 'design_proposals'
            ? renderDesignProposals(value)
            : `<p style="margin: 0; line-height: 1.6;">${escapeHtml(value)}</p>`;
        return `
            <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border);">
                <h4 style="font-size: 13px; font-weight: 600; margin: 0 0 8px;">${section.label}</h4>
                ${content}
            </div>
        `;
    }).join('');

    const meta = `
        <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-bottom: 12px;">
            <span>${_t('dashboard.report.meta.language')}: ${escapeHtml(getLanguageLabel(report.language || ''))}</span>
            <span>${report.generated_at ? formatDate(report.generated_at) : '-'}</span>
        </div>
    `;

    document.getElementById('analysis-content').innerHTML = `
        <div style="padding: 16px;">
            <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 8px;">${escapeHtml(report.title || report.report_name || _t('dashboard.report.titleFallback'))}</h3>
            ${meta}
            ${blocks || `<p style="color: var(--text-muted);">${_t('dashboard.report.empty')}</p>`}
        </div>
    `;
}

function renderDesignProposals(value) {
    const parsed = parseReportJson(value);
    if (Array.isArray(parsed)) {
        const items = parsed.map(item => {
            if (typeof item === 'string') {
                return `<li>${escapeHtml(item)}</li>`;
            }
            const title = escapeHtml(item.concept_name || item.title || '');
            const desc = escapeHtml(item.description || item.rationale || '');
            return `<li><strong>${title || _t('dashboard.report.unnamed')}</strong>${desc ? ` - ${desc}` : ''}</li>`;
        }).join('');
        return `<ul style="margin: 0 0 0 16px; line-height: 1.6;">${items}</ul>`;
    }
    if (parsed && typeof parsed === 'object') {
        return `<pre style="margin: 0; white-space: pre-wrap;">${escapeHtml(JSON.stringify(parsed, null, 2))}</pre>`;
    }
    return `<p style="margin: 0; line-height: 1.6;">${escapeHtml(String(value))}</p>`;
}

function parseReportJson(value) {
    if (!value) return null;
    if (typeof value === 'object') return value;
    try {
        return JSON.parse(value);
    } catch (error) {
        return value;
    }
}

// @MX:WARN: [AUTO] Async report loading with race condition - rapid language changes may cause stale cache
// @MX:REASON: Multiple concurrent requests can overwrite cache inconsistently if user switches languages quickly
async function loadReportForCurrentSession(force) {
    const session = reportState.currentSessionData;
    if (!session) {
        setReportMessage('dashboard.report.selectSession');
        return;
    }
    if (session.status !== 'completed') {
        setReportMessage('dashboard.report.pending');
        return;
    }

    const language = getCurrentLanguage();
    const reportName = `session_${session.id}`;
    const cache = reportState.reportCache;
    if (!force && cache.sessionId === session.id && cache.language === language && cache.data) {
        renderReport(cache.data);
        return;
    }

    setReportMessage('dashboard.report.loading');
    try {
    const params = new URLSearchParams({
        project_id: session.project_id,
        report_type: 'trend_analysis',
        report_name: reportName,
        language: language
    });
        const res = await fetch(`/api/v1/reports?${params.toString()}`);
        if (res.status === 404) {
            resetReportCache();
            setReportMessage('dashboard.report.notFound');
            return;
        }
        if (!res.ok) {
            throw new Error('Report fetch failed');
        }
        const data = await res.json();
        reportState.reportCache = {
            sessionId: session.id,
            language: language,
            data: data
        };
        renderReport(data);
    } catch (error) {
        console.error('Report load error:', error);
        setReportMessage('dashboard.report.fetchFailed');
    }
}

function refreshReportOnLanguageChange() {
    resetReportCache();
    if (reportState.activeTab === 'analysis') {
        loadReportForCurrentSession(true);
    }
}

function getTypeLabel(type) {
    const labels = {
        'design': _t('library.types.design'),
        'model': _t('library.types.model'),
        'blueprint': _t('library.types.blueprint'),
        'sketch': _t('library.types.blueprint'),
        'layout': _t('library.types.blueprint'),
        'pattern': _t('library.types.blueprint')
    };
    return labels[type] || type || '';
}

function getImageLabel(img) {
    return img.title || getTypeLabel(img.type);
}

function getImageUrl(img) {
    if (img.url) return img.url;
    if (img.path) return img.path;
    if (img.image_base64) return `data:image/jpeg;base64,${img.image_base64}`;
    return '';
}

function getCurrentProjectName() {
    const project = reportState.projects.find(p => p.id === reportState.currentProjectId);
    return project ? (project.title || project.name || _t('common.noTitle')) : '';
}

function openImageModal(image) {
    currentImage = image;
    document.getElementById('modal-image').src = getImageUrl(currentImage);
    document.getElementById('modal-image').alt = getImageLabel(currentImage);
    document.getElementById('modal-title').textContent = currentImage.title || _t('library.labels.untitled');
    document.getElementById('modal-type').textContent = getTypeLabel(currentImage.type);
    document.getElementById('modal-session').textContent = currentImage.session_title || '-';
    document.getElementById('modal-project').textContent = currentImage.project_name || '-';
    document.getElementById('modal-created').textContent = formatDate(currentImage.created_at);
    document.getElementById('modal-prompt').textContent = currentImage.prompt || '-';
    document.getElementById('image-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    document.getElementById('image-modal').classList.remove('active');
    document.body.style.overflow = '';
    currentImage = null;
}

async function downloadImage() {
    if (!currentImage) return;
    const imageUrl = getImageUrl(currentImage);
    if (!imageUrl) return;
    if (imageUrl.startsWith('data:')) {
        const a = document.createElement('a');
        a.href = imageUrl;
        a.download = currentImage.filename || 'image.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        return;
    }
    try {
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = currentImage.filename || 'image.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Download failed:', error);
    }
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeImageModal();
});

const modalEl = document.getElementById('image-modal');
if (modalEl) {
    modalEl.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal-overlay')) closeImageModal();
    });
}

window.setupTabHandlers = setupTabHandlers;
window.loadTabContents = loadTabContents;
window.loadReportForCurrentSession = loadReportForCurrentSession;
window.refreshReportOnLanguageChange = refreshReportOnLanguageChange;
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.downloadImage = downloadImage;
})();
