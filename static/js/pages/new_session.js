// Use _t to avoid conflict with i18n.js global t
const _t = (key, params) => window.t ? window.t(key, params) : key;
const pageElement = document.getElementById('new-session-page');
const projectId = parseInt(pageElement?.dataset.projectId || '0', 10);

function addUrlInput() {
    const container = document.getElementById('url-inputs-container');
    const newRow = document.createElement('div');
    newRow.style.display = 'flex';
    newRow.style.gap = '0.5rem';
    newRow.style.marginBottom = '0.5rem';
    newRow.className = 'url-input-row';
    newRow.innerHTML = `
        <input type="url" class="url-input" placeholder="${_t('newSession.inputs.urlPlaceholder')}" style="flex: 1;">
        <button type="button" onclick="removeUrlInput(this)" class="btn btn-sm btn-outline url-remove-btn" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; color: var(--color-danger);">${_t('common.delete')}</button>
    `;
    container.appendChild(newRow);
}

function removeUrlInput(button) {
    const rows = document.querySelectorAll('.url-input-row');
    if (rows.length > 1) {
        button.closest('.url-input-row').remove();
    } else {
        alert(_t('newSession.messages.minUrl'));
    }
}

function selectAllCrawlers() {
    document.querySelectorAll('input[name="crawler"]:not(:disabled)').forEach(cb => cb.checked = true);
}

function deselectAllCrawlers() {
    document.querySelectorAll('input[name="crawler"]').forEach(cb => cb.checked = false);
}

function toggleBlueprintOptions() {
    const show = document.getElementById('generate-blueprints').checked;
    document.getElementById('blueprint-options').style.display = show ? 'block' : 'none';
}

function collectFilters() {
    return {
        gender: document.getElementById('filter-gender').value || null,
        age_group: document.getElementById('filter-age').value || null,
        season: document.getElementById('filter-season').value || null,
        category: document.getElementById('filter-category').value || null
    };
}

function collectCrawlerConfig() {
    const selectedCrawlers = Array.from(document.querySelectorAll('input[name="crawler"]:checked')).map(cb => cb.value);
    return {
        crawlers: selectedCrawlers,
        start_date: document.getElementById('start-date').value || null,
        end_date: document.getElementById('end-date').value || null,
        max_items_per_source: parseInt(document.getElementById('max-items').value, 10) || 100
    };
}

function parseKeywords(value) {
    if (!value) return [];
    return value.split(',').map(k => k.trim()).filter(Boolean);
}

function updateUrlInputsLocale() {
    document.querySelectorAll('.url-input').forEach(input => {
        input.placeholder = _t('newSession.inputs.urlPlaceholder');
    });
    document.querySelectorAll('.url-remove-btn').forEach(btn => {
        btn.textContent = _t('common.delete');
    });
}

document.getElementById('generate-blueprints').addEventListener('change', toggleBlueprintOptions);

document.getElementById('session-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const sessionTitle = document.getElementById('session-title').value.trim();
    const sessionDescription = document.getElementById('session-description').value.trim();
    if (!sessionTitle || !sessionDescription) {
        alert(_t('newSession.messages.required'));
        return;
    }

    const userKeywords = parseKeywords(document.getElementById('user-keywords').value.trim());
    const inputText = document.getElementById('input-text').value.trim();
    const urlInputs = Array.from(document.querySelectorAll('.url-input'))
        .map(input => input.value.trim())
        .filter(url => url !== '');

    const crawlerConfig = collectCrawlerConfig();

    try {
        const res = await fetch('/api/v1/sessions/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: projectId,
                session_title: sessionTitle,
                description: sessionDescription,
                user_keywords: userKeywords.length > 0 ? userKeywords : null,
                filters: collectFilters(),
                input_text: inputText || null,
                input_urls: urlInputs,
                crawler_config: crawlerConfig,
                auto_start: document.getElementById('auto-start').checked,
                generate_images: document.getElementById('generate-images').checked,
                generate_blueprints: document.getElementById('generate-blueprints').checked,
                blueprint_size_system: document.getElementById('blueprint-size-system').value,
                blueprint_size: document.getElementById('blueprint-size').value
            })
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || _t('newSession.messages.createFailed'));
        }

        const session = await res.json();
        const files = document.getElementById('input-files').files;

        if (files.length > 0) {
            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file);
            }
            await fetch(`/api/v1/sessions/${session.id}/upload-files`, {
                method: 'POST',
                body: formData
            });
        }

        if (document.getElementById('auto-start').checked) {
            await fetch(`/api/v1/sessions/${session.id}/run-analysis`, { method: 'POST' });
        }

        alert(_t('newSession.messages.created'));
        window.location.href = `/sessions/${session.id}`;
    } catch (error) {
        console.error('Session create error:', error);
        alert(_t('newSession.messages.createError', { error: error.message }));
    }
});

function initNewSession() {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);

    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    document.getElementById('start-date').value = formatDate(oneMonthAgo);
    document.getElementById('end-date').value = formatDate(today);
    toggleBlueprintOptions();
    updateUrlInputsLocale();
}

document.addEventListener('DOMContentLoaded', () => {
    // Wait for i18n to be ready before initializing
    if (window.i18n && window.i18n.ready) {
        initNewSession();
    } else {
        window.addEventListener('i18nReady', () => initNewSession(), { once: true });
    }
});

window.addEventListener('languageChanged', updateUrlInputsLocale);

// Expose functions to global scope for onclick handlers
window.addUrlInput = addUrlInput;
window.removeUrlInput = removeUrlInput;
window.selectAllCrawlers = selectAllCrawlers;
window.deselectAllCrawlers = deselectAllCrawlers;
