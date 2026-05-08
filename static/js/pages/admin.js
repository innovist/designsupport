/**
 * Admin Console JavaScript
 *
 * Handles admin console interactivity including:
 * - Sidebar toggle
 * - Modal management
 * - Form validation
 * - API calls to admin endpoints
 * - Skeleton loading management
 * - i18n integration
 */

// ============================================================================
// Constants
// ============================================================================

const API_ENDPOINTS = {
    providers: '/api/admin/providers/',
    models: '/api/admin/models/',
    policies: '/api/admin/policies/',
    promptPolicies: '/api/admin/prompt-policies/',
    metrics: '/api/admin/metrics/',
    auditLogs: '/api/admin/audit-logs/',
    rollback: '/api/admin/rollback/',
    jobQueue: '/api/admin/job-queue/',
};

// ============================================================================
// Sidebar Toggle
// ============================================================================

class SidebarToggle {
    constructor() {
        this.sidebar = document.querySelector('.admin-sidebar');
        this.toggleButton = document.querySelector('.sidebar-toggle');
        this.mainContent = document.querySelector('.admin-main');

        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => this.toggle());
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 &&
                !this.sidebar.contains(e.target) &&
                !this.toggleButton.contains(e.target) &&
                this.sidebar.classList.contains('open')) {
                this.close();
            }
        });
    }

    toggle() {
        this.sidebar.classList.toggle('open');
    }

    open() {
        this.sidebar.classList.add('open');
    }

    close() {
        this.sidebar.classList.remove('open');
    }
}

// ============================================================================
// Modal Management
// ============================================================================

class ModalManager {
    constructor() {
        this.modals = document.querySelectorAll('.modal');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Open modals
        document.querySelectorAll('[data-action^="create-"], [data-action^="edit-"], [data-action^="view-"]').forEach(button => {
            button.addEventListener('click', (e) => this.openModal(e));
        });

        // Close modals
        document.querySelectorAll('[data-action="close-modal"]').forEach(button => {
            button.addEventListener('click', () => this.closeAllModals());
        });

        // Close on backdrop click
        this.modals.forEach(modal => {
            const backdrop = modal.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => this.closeModal(modal));
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    openModal(event) {
        const action = event.currentTarget.dataset.action;
        const modalId = this.getModalId(action);

        if (modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';

                // Focus first focusable element
                const firstFocusable = this.getFirstFocusableElement(modal);
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }
        }
    }

    closeModal(modal) {
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    closeAllModals() {
        this.modals.forEach(modal => this.closeModal(modal));
    }

    getModalId(action) {
        const modalMap = {
            'create-provider': 'provider-modal',
            'edit-provider': 'provider-modal',
            'create-model': 'model-modal',
            'edit-model': 'model-modal',
            'create-policy': 'policy-modal',
            'edit-policy': 'policy-modal',
            'create-prompt-policy': 'prompt-policy-modal',
            'edit-prompt-policy': 'prompt-policy-modal',
            'view-diff': 'diff-modal',
            'compare-version': null, // Handled separately
            'rollback-to': 'rollback-modal',
            'view-details': 'job-details-modal',
        };
        return modalMap[action];
    }

    getFirstFocusableElement(modal) {
        const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        return modal.querySelector(focusableSelectors);
    }
}

// ============================================================================
// Form Validation
// ============================================================================

class FormValidator {
    constructor(form) {
        this.form = form;
        this.setupValidation();
    }

    setupValidation() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Real-time validation
        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => {
                if (field.classList.contains('error')) {
                    this.validateField(field);
                }
            });
        });
    }

    handleSubmit(event) {
        if (!this.validateForm()) {
            event.preventDefault();
            return false;
        }
        return true;
    }

    validateForm() {
        let isValid = true;
        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        return isValid;
    }

    validateField(field) {
        if (field.hasAttribute('required') && !field.value.trim()) {
            this.showError(field, 'This field is required');
            return false;
        }

        if (field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                this.showError(field, 'Please enter a valid email address');
                return false;
            }
        }

        if (field.type === 'url' && field.value) {
            try {
                new URL(field.value);
            } catch {
                this.showError(field, 'Please enter a valid URL');
                return false;
            }
        }

        this.clearError(field);
        return true;
    }

    showError(field, message) {
        field.classList.add('error');
        field.setAttribute('aria-invalid', 'true');

        let errorElement = field.parentElement.querySelector('.error-message');
        if (!errorElement) {
            errorElement = document.createElement('span');
            errorElement.className = 'error-message';
            errorElement.setAttribute('role', 'alert');
            field.parentElement.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }

    clearError(field) {
        field.classList.remove('error');
        field.removeAttribute('aria-invalid');

        const errorElement = field.parentElement.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// ============================================================================
// API Client
// ============================================================================

class AdminAPIClient {
    async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(endpoint, finalOptions);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    async getProviders() {
        return this.request(API_ENDPOINTS.providers);
    }

    async createProvider(data) {
        return this.request(API_ENDPOINTS.providers, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateProvider(id, data) {
        return this.request(`${API_ENDPOINTS.providers}${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deactivateProvider(id) {
        return this.request(`${API_ENDPOINTS.providers}${id}/deactivate/`, {
            method: 'POST',
        });
    }

    async getModels(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`${API_ENDPOINTS.models}?${queryString}`);
    }

    async createModel(data) {
        return this.request(API_ENDPOINTS.models, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateModel(id, data) {
        return this.request(`${API_ENDPOINTS.models}${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async activateModel(id) {
        return this.request(`${API_ENDPOINTS.models}${id}/activate/`, {
            method: 'POST',
        });
    }

    async deactivateModel(id) {
        return this.request(`${API_ENDPOINTS.models}${id}/deactivate/`, {
            method: 'POST',
        });
    }

    async getMetrics(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`${API_ENDPOINTS.metrics}?${queryString}`);
    }

    async getAuditLogs(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`${API_ENDPOINTS.auditLogs}?${queryString}`);
    }

    async rollbackPolicy(policyType, featureKey, toVersion, reason) {
        return this.request(API_ENDPOINTS.rollback, {
            method: 'POST',
            body: JSON.stringify({
                policy_type: policyType,
                feature_key: featureKey,
                to_version: toVersion,
                reason,
            }),
        });
    }

    async getJobQueue(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`${API_ENDPOINTS.jobQueue}?${queryString}`);
    }

    async retryJob(jobId) {
        return this.request(`${API_ENDPOINTS.jobQueue}${jobId}/retry/`, {
            method: 'POST',
        });
    }

    async cancelJob(jobId) {
        return this.request(`${API_ENDPOINTS.jobQueue}${jobId}/cancel/`, {
            method: 'POST',
        });
    }
}

// ============================================================================
// Skeleton Loading Management
// ============================================================================

class SkeletonLoader {
    constructor(container) {
        this.container = container;
    }

    show() {
        this.container.classList.add('skeleton-loading');
        this.container.setAttribute('aria-busy', 'true');
    }

    hide() {
        this.container.classList.remove('skeleton-loading');
        this.container.removeAttribute('aria-busy');
    }

    static replaceWithContent(skeletonElement, contentElement) {
        skeletonElement.replaceWith(contentElement);
    }
}

// ============================================================================
// i18n Integration
// ============================================================================

class I18nManager {
    constructor() {
        this.currentLocale = document.documentElement.lang || 'en';
        this.translations = {};
        this.loadTranslations();
    }

    async loadTranslations() {
        try {
            const response = await fetch(`/static/i18n/${this.currentLocale}.json`);
            this.translations = await response.json();
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }

    t(key) {
        const keys = key.split('.');
        let value = this.translations;

        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                return key;
            }
        }

        return value || key;
    }

    updatePageLocale(locale) {
        this.currentLocale = locale;
        document.documentElement.lang = locale;
        this.loadTranslations();
        this.updateAllTranslations();
    }

    updateAllTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });
    }
}

// ============================================================================
// Initialize
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    const sidebar = new SidebarToggle();
    const modals = new ModalManager();
    const i18n = new I18nManager();

    // Initialize form validators
    document.querySelectorAll('form').forEach(form => {
        new FormValidator(form);
    });

    // Initialize API client
    const api = new AdminAPIClient();

    // Make components available globally for debugging
    window.adminConsole = {
        sidebar,
        modals,
        i18n,
        api,
    };
});
