// Use _t to avoid conflict with i18n.js global t
const _t = (key, params) => window.t ? window.t(key, params) : key;
let images = [];
let projects = [];
let sessions = [];
let currentPage = 1;
let totalPages = 1;
let currentImage = null;
const PAGE_SIZE = 24;

async function initLibrary() {
    await Promise.all([loadProjects(), loadSessions()]);
    await loadImages();
}

document.addEventListener('DOMContentLoaded', () => {
    // Wait for i18n to be ready before loading data
    if (window.i18n && window.i18n.ready) {
        initLibrary();
    } else {
        window.addEventListener('i18nReady', () => initLibrary(), { once: true });
    }
});

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        if (response.ok) {
            projects = await response.json();
            const select = document.getElementById('filter-project');
            projects.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = p.name || _t('common.noTitle');
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (response.ok) {
            sessions = await response.json();
            const select = document.getElementById('filter-session');
            sessions.forEach(s => {
                const option = document.createElement('option');
                option.value = s.id;
                const briefTitle = s.brief && s.brief.purpose ? s.brief.purpose : null;
                option.textContent = briefTitle || _t('common.noTitle');
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

async function loadImages() {
    showLoading(true);

    try {
        const params = new URLSearchParams();

        const projectId = document.getElementById('filter-project').value;
        const sessionId = document.getElementById('filter-session').value;
        const imageType = document.getElementById('filter-type').value;
        const dateFrom = document.getElementById('filter-date-from').value;
        const dateTo = document.getElementById('filter-date-to').value;
        const sortBy = document.getElementById('filter-sort').value;

        if (projectId) params.append('project_id', projectId);
        if (sessionId) params.append('session_id', sessionId);
        if (imageType) params.append('image_type', imageType);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        params.append('sort', sortBy);
        params.append('page', currentPage);
        params.append('limit', PAGE_SIZE);

        const response = await fetch(`/api/library?${params}`);

        if (response.ok) {
            const data = await response.json();
            images = data.images || [];
            totalPages = Math.ceil((data.total || 0) / PAGE_SIZE);

            updateStats(data.stats || {});
            renderImages();
            updatePagination();
        } else {
            images = [];
            showEmpty();
        }
    } catch (error) {
        console.error('Failed to load images:', error);
        images = [];
        showEmpty();
    }

    showLoading(false);
}

function updateStats(stats) {
    document.getElementById('total-count').textContent = stats.total || 0;
    document.getElementById('design-count').textContent = stats.design || 0;
    document.getElementById('model-count').textContent = stats.model || 0;
    document.getElementById('blueprint-count').textContent = stats.blueprint || 0;
}

function renderImages() {
    const grid = document.getElementById('image-grid');
    const emptyState = document.getElementById('empty-state');

    if (images.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    grid.innerHTML = images.map(img => `
        <div class="image-card" onclick="openModal(${JSON.stringify(img).replace(/"/g, '&quot;')})">
            <div class="image-wrapper">
                <img src="${getImageUrl(img)}" alt="${getImageLabel(img)}" loading="lazy">
                <span class="image-type-badge ${img.type}">${getTypeLabel(img.type)}</span>
            </div>
            <div class="image-info">
                <div class="image-title">${img.title || _t('library.labels.untitled')}</div>
                <div class="image-meta">${formatDate(img.created_at)}</div>
            </div>
        </div>
    `).join('');
}

function getTypeLabel(type) {
    const labels = {
        'design': _t('library.types.design'),
        'model': _t('library.types.model'),
        'blueprint': _t('library.types.blueprint')
    };
    return labels[type] || type;
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

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(window.i18n.getNumberLocale());
}

function updatePagination() {
    const pagination = document.getElementById('pagination');
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }

    pagination.style.display = 'flex';
    pageInfo.textContent = `${currentPage} / ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadImages();
}

function applyFilters() {
    currentPage = 1;
    loadImages();
}

function resetFilters() {
    document.getElementById('filter-project').value = '';
    document.getElementById('filter-session').value = '';
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-sort').value = 'created_at_desc';
    currentPage = 1;
    loadImages();
}

function openModal(image) {
    currentImage = typeof image === 'string' ? JSON.parse(image) : image;

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

function closeModal() {
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

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
    if (show) {
        document.getElementById('image-grid').innerHTML = '';
        document.getElementById('empty-state').style.display = 'none';
    }
}

function showEmpty() {
    document.getElementById('image-grid').innerHTML = '';
    document.getElementById('empty-state').style.display = 'block';
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

document.getElementById('image-modal').addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

window.addEventListener('languageChanged', () => {
    renderImages();
    updatePagination();
    if (currentImage) {
        openModal(currentImage);
    }
});

// Expose functions to global scope for onclick handlers
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.goToPage = goToPage;
window.openModal = openModal;
window.closeModal = closeModal;
window.downloadImage = downloadImage;
