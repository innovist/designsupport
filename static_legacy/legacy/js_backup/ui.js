// UI Management Module

class UIManager {
    constructor() {
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        this.notificationContainer = document.getElementById('notification-container');
    }

    // Loading overlay
    showLoading(text = null) {
        this.loadingText.textContent = text || (window.t ? t('ui.processing') : '처리 중...');
        this.loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    }

    // Notifications
    showNotification(message, type = 'success', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        this.notificationContainer.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);

        // Click to remove
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error', 10000);
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    // Section navigation
    switchSection(sectionId) {
        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${sectionId}`) {
                link.classList.add('active');
            }
        });

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');
    }

    // Form helpers
    getFormData(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Handle checkboxes
            if (form.querySelector(`input[type="checkbox"][name="${key}"]`)) {
                if (!data[key]) data[key] = [];
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        // Add unchecked checkboxes
        form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            if (!checkbox.checked && !data[checkbox.name]) {
                data[checkbox.name] = false;
            }
        });

        return data;
    }

    clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }
    }

    // Image display helpers
    displayImageResults(results, containerId, title = null) {
        const container = document.getElementById(containerId);
        const _t = window.t || ((k) => k);
        const displayTitle = title || _t('imageGeneration.results.title');

        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${_t('imageGeneration.results.noResults')}</p>
                </div>
            `;
            return;
        }

        let html = `<h3>${displayTitle}</h3><div class="image-grid">`;

        results.forEach((imageData, index) => {
            const imageBase64 = typeof imageData === 'string' ? imageData : imageData.image;
            html += `
                <div class="image-card">
                    <img src="data:image/jpeg;base64,${imageBase64}" alt="Generated image ${index + 1}">
                    <div class="image-info">
                        <div class="image-title">${_t('ui.image')} ${index + 1}</div>
                        ${imageData.metadata ? `
                            <div class="image-meta">
                                ${_t('ui.model')}: ${imageData.model_used || 'N/A'}<br>
                                ${_t('ui.generationTime')}: ${(imageData.generation_time || 0).toFixed(2)}${_t('ui.seconds')}
                            </div>
                        ` : ''}
                    </div>
                    <div style="padding: 0 1rem 1rem;">
                        <button class="btn btn-secondary" onclick="uiManager.downloadImage('image-${index}', '${imageBase64}')">
                            ${_t('common.download')}
                        </button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    downloadImage(filename, base64Data) {
        const link = document.createElement('a');
        link.download = `${filename}.jpg`;
        link.href = `data:image/jpeg;base64,${base64Data}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Trend results display
    displayTrendResults(results, containerId) {
        const container = document.getElementById(containerId);
        const _t = window.t || ((k) => k);

        if (!results || !results.analyses || results.analyses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${_t('trendAnalysis.results.noResults')}</p>
                </div>
            `;
            return;
        }

        let html = '<div class="trend-results">';

        results.analyses.forEach(analysis => {
            html += `
                <div class="trend-item">
                    <div class="trend-title">${analysis.model || _t('ui.model')}</div>
                    <div class="trend-summary">${analysis.analysis || ''}</div>
                    <div class="trend-tags">
                        ${analysis.trends ? analysis.trends.map(trend =>
                            `<span class="trend-tag">${trend}</span>`
                        ).join('') : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    // Blueprint results display
    displayBlueprintResults(results, containerId) {
        const container = document.getElementById(containerId);
        const _t = window.t || ((k) => k);

        if (!results) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${_t('blueprint.results.noResults')}</p>
                </div>
            `;
            return;
        }

        let html = `
            <div class="blueprint-tabs">
                <button class="tab-btn active" onclick="uiManager.switchTab('pieces')">${_t('blueprint.tabs.pieces')}</button>
                <button class="tab-btn" onclick="uiManager.switchTab('layout')">${_t('blueprint.tabs.layout')}</button>
                <button class="tab-btn" onclick="uiManager.switchTab('instructions')">${_t('blueprint.tabs.instructions')}</button>
                <button class="tab-btn" onclick="uiManager.switchTab('materials')">${_t('blueprint.tabs.materials')}</button>
            </div>
        `;

        // Pattern pieces tab
        html += '<div id="pieces-tab" class="tab-content active">';
        if (results.pattern_pieces && results.pattern_pieces.length > 0) {
            results.pattern_pieces.forEach((piece, index) => {
                html += `
                    <div class="pattern-piece">
                        <div class="pattern-header">
                            ${piece.name} (x${piece.piece_count})
                        </div>
                        <div class="pattern-body">
                            <img src="data:image/png;base64,${piece.image}"
                                 alt="${piece.name}"
                                 class="pattern-image">
                            <p style="margin-top: 1rem;">${piece.instructions || ''}</p>
                            <button class="btn btn-secondary"
                                    onclick="uiManager.downloadImage('pattern-${index}', '${piece.image}')">
                                ${_t('common.download')}
                            </button>
                        </div>
                    </div>
                `;
            });
        }
        html += '</div>';

        // Layout diagram tab
        html += '<div id="layout-tab" class="tab-content">';
        if (results.layout_diagram) {
            html += `
                <img src="data:image/png;base64,${results.layout_diagram}"
                     alt="Layout Diagram"
                     class="pattern-image"
                     style="max-width: 100%;">
                <button class="btn btn-secondary"
                        onclick="uiManager.downloadImage('layout', '${results.layout_diagram}')">
                    ${_t('common.download')}
                </button>
            `;
        }
        html += '</div>';

        // Instructions tab
        html += '<div id="instructions-tab" class="tab-content">';
        if (results.instructions) {
            html += `<div style="white-space: pre-wrap;">${results.instructions}</div>`;
        }
        html += '</div>';

        // Materials tab
        html += '<div id="materials-tab" class="tab-content">';
        if (results.material_requirements) {
            if (results.material_requirements.fabric) {
                html += `
                    <h4>${_t('blueprint.materials.fabric')}</h4>
                    <p>${results.material_requirements.fabric.length}cm x ${results.material_requirements.fabric.width}cm</p>
                `;
            }
            if (results.material_requirements.other_materials) {
                html += `<h4>${_t('blueprint.materials.other')}</h4>`;
                html += '<ul class="material-list">';
                Object.entries(results.material_requirements.other_materials).forEach(([material, info]) => {
                    if (info.amount > 0) {
                        html += `<li>${material}: ${info.amount} ${info.unit}</li>`;
                    }
                });
                html += '</ul>';
            }
        }
        html += '</div>';

        container.innerHTML = html;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(tabName)) {
                btn.classList.add('active');
            }
        });

        // Update tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    // Crawler status display
    displayCrawlStatus(status, containerId) {
        const container = document.getElementById(containerId);
        const _t = window.t || ((k) => k);

        let html = `
            <div class="crawl-status">
                <h4>${_t('crawler.status.title')}</h4>
                <p>${_t('crawler.status.status')}: ${status.status || _t('ui.unknown')}</p>
                <p>${_t('crawler.status.progress')}: ${status.progress || 0}%</p>
                <p>${_t('crawler.status.processed')}: ${status.processed || 0} / ${status.total || 0}</p>
                ${status.error ? `<p style="color: var(--error-color);">${_t('crawler.status.error')}: ${status.error}</p>` : ''}
            </div>
        `;

        if (status.progress !== undefined) {
            html += `
                <div class="status-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${status.progress}%"></div>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    displayCrawledItems(items, containerId) {
        const container = document.getElementById(containerId);
        const _t = window.t || ((k) => k);

        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>${_t('crawler.results.noResults')}</p>
                </div>
            `;
            return;
        }

        let html = '<div class="crawled-items">';

        items.slice(0, 20).forEach(item => {  // Show first 20 items
            html += `
                <div class="crawled-item">
                    <div class="item-title">${item.title || _t('ui.noTitle')}</div>
                    <div class="item-source">${_t('crawler.results.source')}: ${item.source || _t('ui.unknown')} | ${item.url ? `<a href="${item.url}" target="_blank">${_t('ui.link')}</a>` : ''}</div>
                    <div class="item-preview">${item.content || item.summary || _t('ui.noContent')}</div>
                </div>
            `;
        });

        if (items.length > 20) {
            html += `<p style="text-align: center; color: var(--medium-gray);">${_t('crawler.results.moreItems', { count: items.length - 20 })}</p>`;
        }

        html += '</div>';
        container.innerHTML = html;
    }
}

// Create global UI manager instance
const uiManager = new UIManager();