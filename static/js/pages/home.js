// Home Page JavaScript
// Use _t to avoid conflict with i18n.js global t
const _t = (key, params) => window.t ? window.t(key, params) : key;

function initHome() {
    updateIdeaChipsLocale();
    loadSystemStatus();
    loadRecentProjects();
    loadRecentImages();
    setupEventHandlers();
}

document.addEventListener('DOMContentLoaded', () => {
    // Wait for i18n to be ready before initializing
    if (window.i18n && window.i18n.ready) {
        initHome();
    } else {
        window.addEventListener('i18nReady', () => initHome(), { once: true });
    }
});

function setupEventHandlers() {
    // Idea chips click handler
    document.querySelectorAll('.idea-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const idea = chip.dataset.idea;
            document.getElementById('trend-idea-input').value = idea;
        });
    });

    // Start button click handler
    document.getElementById('idea-start-btn').addEventListener('click', () => {
        const idea = document.getElementById('trend-idea-input').value.trim();
        if (idea) {
            // Navigate to projects page with idea as query param
            window.location.href = `/projects?idea=${encodeURIComponent(idea)}`;
        } else {
            window.location.href = '/projects';
        }
    });

    // Enter key in search input
    document.getElementById('trend-idea-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('idea-start-btn').click();
        }
    });
}

function updateIdeaChipsLocale() {
    document.querySelectorAll('.idea-chip').forEach(chip => {
        const key = chip.dataset.ideaKey;
        if (!key) return;
        const translated = _t(key);
        if (translated && translated !== key) {
            chip.dataset.idea = translated;
        }
    });
}

async function loadSystemStatus() {
    try {
        // Load crawler status
        const crawlerRes = await fetch('/api/v1/crawlers/list');
        if (crawlerRes.ok) {
            const data = await crawlerRes.json();
            const enabled = data.counts?.enabled || 0;
            const total = data.counts?.total || 0;
            document.getElementById('crawler-status').textContent = `${enabled}/${total} ${_t('home.status.active')}`;
        }
    } catch (e) {
        document.getElementById('crawler-status').textContent = _t('home.status.error');
    }

    // Check Gemini API status
    try {
        const geminiRes = await fetch('/api/v1/settings/api-status');
        if (geminiRes.ok) {
            const status = await geminiRes.json();
            const geminiIcon = document.getElementById('gemini-status-icon');
            const geminiStatus = document.getElementById('gemini-status');

            if (status.gemini?.configured) {
                geminiIcon.textContent = '✓';
                geminiIcon.className = 'status-icon active';
                geminiStatus.textContent = _t('home.status.connected');
            } else {
                geminiIcon.textContent = '!';
                geminiIcon.className = 'status-icon error';
                geminiStatus.textContent = _t('home.status.notConfigured');
            }

            const imageIcon = document.getElementById('image-status-icon');
            const imageStatus = document.getElementById('image-status');

            const hasImageApi = status.seedream?.configured || status.nano_banana?.configured || status.zimage?.configured;
            if (hasImageApi) {
                imageIcon.textContent = '✓';
                imageIcon.className = 'status-icon active';
                imageStatus.textContent = _t('home.status.connected');
            } else {
                imageIcon.textContent = '!';
                imageIcon.className = 'status-icon error';
                imageStatus.textContent = _t('home.status.notConfigured');
            }
        }
    } catch (e) {
        console.error('API status check failed:', e);
    }
}

async function loadRecentProjects() {
    const container = document.getElementById('recent-projects');

    try {
        const res = await fetch('/api/v1/projects/?limit=4');
        if (res.ok) {
            const projects = await res.json();

            if (!projects.length) {
                container.innerHTML = `
                    <div class="empty-state">
                        ${_t('home.recentProjects.empty')}
                        <br>
                        <a href="/projects" class="btn btn-primary btn-sm" style="margin-top: 12px;">${_t('home.recentProjects.createFirst')}</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = projects.map(p => `
                <a href="/projects/${p.id}" class="project-card">
                    <div class="title-row">
                        <span class="name">${escapeHtml(p.title || _t('common.noTitle'))}</span>
                        <span class="session-count">${p.session_count || 0} ${_t('home.recentProjects.sessions')}</span>
                    </div>
                    <div class="project-desc">${escapeHtml(p.description || _t('common.noDescription'))}</div>
                    <div class="project-footer">
                        <span>${formatDate(p.created_at)}</span>
                        <span>${getStatusText(p.status)}</span>
                    </div>
                </a>
            `).join('');
        }
    } catch (e) {
        console.error('Failed to load projects:', e);
        container.innerHTML = `<div class="empty-state">${_t('home.recentProjects.error')}</div>`;
    }
}

async function loadRecentImages() {
    const container = document.getElementById('recent-images');
    const mosaic = document.getElementById('hero-mosaic');
    const metaCount = document.getElementById('hero-meta-count');

    try {
        const res = await fetch('/api/library?limit=8&sort=created_at_desc');
        if (res.ok) {
            const data = await res.json();
            const images = data.images || [];

            if (!images.length) {
                container.innerHTML = `<div class="empty-state">${_t('home.recentImages.empty')}</div>`;
                return;
            }

            // Update hero mosaic with first 4 images
            if (images.length > 0) {
                const mosaicImages = images.slice(0, 4);
                mosaic.innerHTML = mosaicImages.map(img => `
                    <div class="hero-tile">
                        <img src="${getImageUrl(img)}" alt="${escapeHtml(img.title || '')}">
                        <span class="tile-label">${getTypeLabel(img.type)}</span>
                    </div>
                `).join('');
                metaCount.textContent = _t('home.hero.recentCount', { count: data.total || images.length });
            }

            // Update recent images grid
            container.innerHTML = images.map(img => `
                <div class="image-card" onclick="window.location.href='/library'">
                    <img src="${getImageUrl(img)}" alt="${escapeHtml(img.title || '')}">
                    <div class="image-label">${escapeHtml(img.title || getTypeLabel(img.type))}</div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Failed to load images:', e);
        container.innerHTML = `<div class="empty-state">${_t('home.recentImages.error')}</div>`;
    }
}

function getImageUrl(img) {
    if (img.url) return img.url;
    if (img.path) return img.path;
    if (img.image_base64) return `data:image/jpeg;base64,${img.image_base64}`;
    return '';
}

function getTypeLabel(type) {
    const labels = {
        'design': _t('library.types.design'),
        'model': _t('library.types.model'),
        'blueprint': _t('library.types.blueprint')
    };
    return labels[type] || type;
}

function getStatusText(status) {
    const map = {
        created: _t('status.created'),
        active: _t('status.active'),
        completed: _t('status.completed'),
        draft: _t('status.draft')
    };
    return map[status] || status || '';
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(window.i18n?.getNumberLocale() || 'ko-KR', {
        month: 'short',
        day: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// Language change handler
window.addEventListener('languageChanged', () => {
    updateIdeaChipsLocale();
    loadSystemStatus();
    loadRecentProjects();
    loadRecentImages();
});
