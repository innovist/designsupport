// @MX:NOTE: [AUTO] Crawler management module that handles data source selection and YouTube channel integration
// @MX:REASON: Provides UI for configuring which fashion data sources to crawl and managing YouTube channel subscriptions
// Crawler and YouTube handlers
(function() {
const crawlerState = window.dashboardState;
const {
    _t,
    escapeHtml,
    getCrawlerLabel
} = window.dashboardUtils;
async function loadCrawlerList() {
    try {
        await loadCrawlerConfig();
        const res = await fetch('/api/v1/crawlers/list');
        if (res.ok) {
            const data = await res.json();
            crawlerState.crawlerList = [];
            if (data.categorized) {
                Object.values(data.categorized).forEach(cat => {
                    crawlerState.crawlerList.push(...cat.crawlers);
                });
            }
            renderCrawlerCheckboxes();
        }
    } catch (e) {
        console.error('Crawler list error:', e);
    }
}
async function loadCrawlerConfig() {
    try {
        const res = await fetch('/api/v1/settings/');
        if (res.ok) {
            const data = await res.json();
            crawlerState.crawlerConfig = data.config || {};
        }
    } catch (e) {
        console.error('Crawler config error:', e);
    }
}
function renderCrawlerCheckboxes() {
    const container = document.getElementById('crawler-checkboxes');
    const searxngConfigured = Boolean(crawlerState.crawlerConfig?.searxng_api_url);
    container.innerHTML = crawlerState.crawlerList.map(c => `
        <label style="display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer; ${c.id === 'searxng' && !searxngConfigured ? 'opacity: 0.6;' : ''}">
            <input type="checkbox" name="crawlers" value="${c.id}" ${c.enabled && (c.id !== 'searxng' || searxngConfigured) ? 'checked' : ''} ${c.id === 'searxng' && !searxngConfigured ? 'disabled' : ''} onchange="onCrawlerChange()">
            ${escapeHtml(getCrawlerLabel(c))}
            ${c.id === 'searxng' && !searxngConfigured ? `<span style="font-size: 10px; color: var(--text-muted);">${escapeHtml(_t('dashboard.crawlers.searxngDisabled'))}</span>` : ''}
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
function selectAllCrawlers() {
    document.querySelectorAll('input[name="crawlers"]').forEach(cb => cb.checked = true);
}
function deselectAllCrawlers() {
    document.querySelectorAll('input[name="crawlers"]').forEach(cb => cb.checked = false);
}
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
// @MX:WARN: [AUTO] YouTube URL parsing with fragile string splitting - lacks comprehensive format validation
// @MX:REASON: Complex URL patterns may not be captured; edge cases could bypass validation
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
function onCrawlerChange() {
    renderYoutubeChannels();
}
window.loadCrawlerList = loadCrawlerList;
window.loadCrawlerConfig = loadCrawlerConfig;
window.renderCrawlerCheckboxes = renderCrawlerCheckboxes;
window.loadCrawlerSummary = loadCrawlerSummary;
window.selectAllCrawlers = selectAllCrawlers;
window.deselectAllCrawlers = deselectAllCrawlers;
window.loadYoutubeChannels = loadYoutubeChannels;
window.renderYoutubeChannels = renderYoutubeChannels;
window.toggleYoutubeChannel = toggleYoutubeChannel;
window.addYoutubeChannel = addYoutubeChannel;
window.removeYoutubeChannel = removeYoutubeChannel;
window.getSelectedYoutubeChannels = getSelectedYoutubeChannels;
window.onCrawlerChange = onCrawlerChange;
})();
