// Project handlers
(function() {
const projectState = window.dashboardState;
const {
    _t,
    escapeHtml,
    getStatusText
} = window.dashboardUtils;

async function loadProjects() {
    try {
        const res = await fetch('/api/v1/projects/');
        if (res.ok) {
            projectState.projects = await res.json();
            renderProjects();
        }
    } catch (e) {
        console.error('Projects load error:', e);
    }
}

function renderProjects() {
    const select = document.getElementById('project-select');
    const placeholder = `<option value="">${_t('dashboard.placeholders.selectProject')}</option>`;
    if (!projectState.projects.length) {
        select.innerHTML = placeholder;
        return;
    }
    select.innerHTML = placeholder + projectState.projects.map(p => `
        <option value="${p.id}" ${projectState.currentProjectId === p.id ? 'selected' : ''}>
            ${escapeHtml(p.title || p.name || _t('common.noTitle'))} (${p.session_count || 0})
        </option>
    `).join('');
}

function onProjectSelect(value) {
    if (value) {
        selectProject(parseInt(value, 10));
        document.getElementById('edit-project-btn').style.display = 'block';
        document.getElementById('delete-project-btn').style.display = 'block';
    } else {
        projectState.currentProjectId = null;
        projectState.currentSessionId = null;
        document.getElementById('add-session-btn').disabled = true;
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
    projectState.currentProjectId = projectId;
    projectState.currentSessionId = null;
    projectState.currentSessionData = null;
    renderProjects();
    document.getElementById('add-session-btn').disabled = false;
    await loadSessions(projectId);
    resetReportPanel();
}

function showCreateProjectModal() {
    document.getElementById('project-modal').style.display = 'flex';
    document.getElementById('project-title').focus();
    updateImageModelSelectors();
}

function closeProjectModal() {
    document.getElementById('project-modal').style.display = 'none';
    document.getElementById('project-form').reset();
}

function showEditProjectModal() {
    if (!projectState.currentProjectId) return;
    const project = projectState.projects.find(p => p.id === projectState.currentProjectId);
    if (!project) return;

    document.getElementById('edit-project-id').value = project.id;
    document.getElementById('edit-project-title').value = project.title || project.name || '';
    document.getElementById('edit-project-desc').value = project.description || '';
    document.getElementById('edit-project-image-model').value = project.preferred_image_model || '';
    document.getElementById('edit-project-modal').style.display = 'flex';
    document.getElementById('edit-project-title').focus();
    updateImageModelSelectors(project.preferred_image_model || '');
}

function closeEditProjectModal() {
    document.getElementById('edit-project-modal').style.display = 'none';
    document.getElementById('edit-project-form').reset();
}

async function createProject() {
    const title = document.getElementById('project-title').value.trim();
    const desc = document.getElementById('project-desc').value.trim();
    const preferredModel = document.getElementById('project-image-model').value || null;
    if (!title) { alert(_t('dashboard.messages.projectNameRequired')); return; }

    try {
        const res = await fetch('/api/v1/projects/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                prompt: title,
                description: desc,
                preferred_image_model: preferredModel
            })
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

async function updateProject() {
    const projectId = document.getElementById('edit-project-id').value;
    const title = document.getElementById('edit-project-title').value.trim();
    const desc = document.getElementById('edit-project-desc').value.trim();
    const preferredModel = document.getElementById('edit-project-image-model').value || null;

    if (!title) { alert(_t('dashboard.messages.projectNameRequired')); return; }

    try {
        const res = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                description: desc,
                preferred_image_model: preferredModel
            })
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
    if (!projectState.currentProjectId) return;
    const project = projectState.projects.find(p => p.id === projectState.currentProjectId);
    const projectName = project ? (project.title || project.name) : '';

    if (!confirm(_t('dashboard.messages.confirmDeleteProject', { name: projectName }))) return;

    try {
        const res = await fetch(`/api/v1/projects/${projectState.currentProjectId}`, { method: 'DELETE' });
        if (res.ok) {
            projectState.currentProjectId = null;
            projectState.currentSessionId = null;
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

function buildImageModelStatusText(status) {
    if (status.gpuAvailable === null) {
        return _t('dashboard.modals.project.gpuDetecting');
    }
    if (status.gpuAvailable) {
        const info = status.gpuInfo ? `(${status.gpuInfo})` : '';
        return _t('dashboard.modals.project.gpuAvailable', { info: info });
    }
    if (!status.gpuInfo) {
        return _t('dashboard.modals.project.gpuUnknown');
    }
    return _t('dashboard.modals.project.gpuUnavailable');
}

function updateImageModelSelectors(selectedValue) {
    const status = projectState.imageModelStatus;
    const selects = [
        { id: 'project-image-model', statusId: 'project-image-model-status' },
        { id: 'edit-project-image-model', statusId: 'edit-project-image-model-status' }
    ];

    selects.forEach(item => {
        const select = document.getElementById(item.id);
        const statusEl = document.getElementById(item.statusId);
        if (!select || !statusEl) return;

        const zimageOption = select.querySelector('option[value="zimage"]');
        if (zimageOption) {
            zimageOption.disabled = !status.zimageAvailable;
        }

        if (selectedValue !== undefined && select.id === 'edit-project-image-model') {
            select.value = selectedValue;
        }

        statusEl.textContent = buildImageModelStatusText(status);
    });
}

async function loadImageModelStatus() {
    try {
        const res = await fetch('/api/v1/settings/image-models');
        if (!res.ok) {
            throw new Error('Image model status fetch failed');
        }
        const data = await res.json();
        projectState.imageModelStatus = {
            gpuAvailable: data.gpu_available,
            gpuInfo: data.gpu_info,
            zimageAvailable: data.zimage_available
        };
    } catch (error) {
        console.error('Image model status error:', error);
        projectState.imageModelStatus = {
            gpuAvailable: false,
            gpuInfo: null,
            zimageAvailable: false
        };
    } finally {
        updateImageModelSelectors();
    }
}

window.loadProjects = loadProjects;
window.renderProjects = renderProjects;
window.onProjectSelect = onProjectSelect;
window.selectProject = selectProject;
window.showCreateProjectModal = showCreateProjectModal;
window.closeProjectModal = closeProjectModal;
window.showEditProjectModal = showEditProjectModal;
window.closeEditProjectModal = closeEditProjectModal;
window.createProject = createProject;
window.updateProject = updateProject;
window.confirmDeleteProject = confirmDeleteProject;
window.loadImageModelStatus = loadImageModelStatus;
window.updateImageModelSelectors = updateImageModelSelectors;
})();
