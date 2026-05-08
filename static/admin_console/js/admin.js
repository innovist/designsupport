/**
 * Admin Console JavaScript
 *
 * Provides interactivity for admin console including:
 * - Form validation
 * - Dynamic updates
 * - Skeleton loading states
 * - i18n support
 * - AJAX operations
 */

(function() {
    'use strict';

    var CONFIG = {
        pagination: {
            defaultPageSize: 20,
            maxPageSize: 100,
        },
        skeleton: {
            minDisplayTime: 500,
        },
        api: {
            timeout: 30000,
            retryAttempts: 3,
        },
    };

    var state = {
        currentFilters: {},
        currentPage: 1,
        isLoading: false,
        skeletonTimer: null,
    };

    function formatNumber(num) {
        return new Intl.NumberFormat('en-US').format(num);
    }

    function formatCurrency(amount, currency) {
        currency = currency || 'USD';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
        }).format(amount);
    }

    function formatDate(dateString) {
        var date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        }).format(date);
    }

    function debounce(func, wait) {
        var timeout = null;
        return function() {
            var args = arguments;
            var ctx = this;
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(function() { func.apply(ctx, args); }, wait);
        };
    }

    function showSkeleton(container) {
        container.classList.add('skeleton-loading');
        state.skeletonTimer = setTimeout(function() {
            container.classList.remove('skeleton-loading');
        }, CONFIG.skeleton.minDisplayTime);
    }

    function hideSkeleton() {
        if (state.skeletonTimer) {
            clearTimeout(state.skeletonTimer);
        }
        var skeletons = document.querySelectorAll('.skeleton-loading');
        skeletons.forEach(function(el) { el.classList.remove('skeleton-loading'); });
    }

    function validateForm(form) {
        var isValid = true;
        var inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(function(input) {
            if (input.hasAttribute('required') && !input.value) {
                showError(input, 'This field is required');
                isValid = false;
            } else if (input.type === 'email' && input.value && !isValidEmail(input.value)) {
                showError(input, 'Please enter a valid email address');
                isValid = false;
            } else if (input.type === 'number' && input.value && !isValidNumber(input.value)) {
                showError(input, 'Please enter a valid number');
                isValid = false;
            } else {
                clearError(input);
            }
        });

        return isValid;
    }

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidNumber(value) {
        return !isNaN(parseFloat(value)) && isFinite(parseFloat(value));
    }

    function showError(input, message) {
        var formGroup = input.closest('.admin-form-group');
        if (formGroup) {
            var errorElement = formGroup.querySelector('.admin-error-message');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'admin-error-message';
                errorElement.style.color = 'var(--admin-error)';
                errorElement.style.fontSize = '0.75rem';
                errorElement.style.marginTop = 'var(--admin-spacing-xs)';
                formGroup.appendChild(errorElement);
            }
            errorElement.textContent = message;
            input.classList.add('admin-input-error');
        }
    }

    function clearError(input) {
        var formGroup = input.closest('.admin-form-group');
        if (formGroup) {
            var errorElement = formGroup.querySelector('.admin-error-message');
            if (errorElement) {
                errorElement.remove();
            }
        }
        input.classList.remove('admin-input-error');
    }

    function fetchWithRetry(url, options) {
        options = options || {};
        var lastError = null;

        var attempt = function(i) {
            if (i >= CONFIG.api.retryAttempts) {
                throw lastError;
            }

            return fetch(url, {
                method: options.method,
                body: options.body,
                headers: Object.assign({}, {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                }, options.headers || {}),
            }).then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                return response;
            }).catch(function(error) {
                lastError = error;
                if (i < CONFIG.api.retryAttempts - 1) {
                    return new Promise(function(resolve) {
                        setTimeout(resolve, Math.pow(2, i) * 1000);
                    }).then(function() { return attempt(i + 1); });
                }
                throw lastError;
            });
        };

        return attempt(0);
    }

    function getCsrfToken() {
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    function initializeFilters() {
        var filterForms = document.querySelectorAll('.admin-filters');

        filterForms.forEach(function(form) {
            var inputs = form.querySelectorAll('input, select');
            inputs.forEach(function(input) {
                input.addEventListener('change', debounce(handleFilterChange, 300));
            });
        });
    }

    function handleFilterChange(event) {
        var input = event.target;
        var form = input.closest('.admin-filters');

        if (form) {
            var formData = new FormData(form);
            var filters = Object.fromEntries(formData.entries());

            state.currentFilters = filters;
            state.currentPage = 1;

            refreshData();
        }
    }

    function refreshData() {
        var url = new URL(window.location.href);
        Object.entries(state.currentFilters).forEach(function(entry) {
            if (entry[1]) {
                url.searchParams.set(entry[0], entry[1]);
            }
        });
        url.searchParams.set('page', state.currentPage.toString());

        var container = document.querySelector('.dashboard-container, .providers-container, .models-container');
        if (container) {
            showSkeleton(container);
        }

        fetchWithRetry(url.toString())
            .then(function(response) { return response.text(); })
            .then(function(html) {
                document.documentElement.innerHTML = html;
                hideSkeleton();
                initializeFilters();
            })
            .catch(function(error) {
                console.error('Failed to refresh data:', error);
                showAlert('error', 'Failed to load data. Please try again.');
                hideSkeleton();
            });
    }

    function initializePagination() {
        var paginationButtons = document.querySelectorAll('.admin-pagination-controls button');

        paginationButtons.forEach(function(button) {
            button.addEventListener('click', function(event) {
                var page = event.currentTarget.dataset.page;
                if (page) {
                    state.currentPage = parseInt(page);
                    refreshData();
                }
            });
        });
    }

    function initializeForms() {
        var forms = document.querySelectorAll('form[data-ajax="true"]');
        forms.forEach(function(form) {
            form.addEventListener('submit', handleFormSubmit);
        });
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        var form = event.target;

        if (!validateForm(form)) {
            return;
        }

        var formData = new FormData(form);
        var data = Object.fromEntries(formData.entries());
        var url = form.action || window.location.href;
        var method = form.method || 'POST';

        var submitButton = form.querySelector('[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Saving...';
        }

        fetchWithRetry(url, {
            method: method,
            body: JSON.stringify(data),
        }).then(function(response) {
            return response.json();
        }).then(function(result) {
            if (result.error) {
                showAlert('error', result.error);
            } else {
                showAlert('success', 'Changes saved successfully');
                if (form.dataset.redirect) {
                    window.location.href = form.dataset.redirect;
                } else {
                    refreshData();
                }
            }
        }).catch(function(error) {
            console.error('Form submission failed:', error);
            showAlert('error', 'Failed to save changes. Please try again.');
        }).finally(function() {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Save';
            }
        });
    }

    function showAlert(type, message) {
        var existingAlerts = document.querySelectorAll('.admin-alert');
        existingAlerts.forEach(function(alert) { alert.remove(); });

        var alert = document.createElement('div');
        alert.className = 'admin-alert admin-alert-' + type;
        alert.innerHTML =
            '<span>' + message + '</span>' +
            '<button type="button" class="admin-alert-close" aria-label="Close alert">&times;</button>';

        var closeButton = alert.querySelector('.admin-alert-close');
        closeButton.addEventListener('click', function() { alert.remove(); });

        var container = document.querySelector('.dashboard-container, .providers-container, .models-container');
        if (container) {
            container.insertBefore(alert, container.firstChild);
        }

        setTimeout(function() { alert.remove(); }, 5000);
    }

    function initializeI18n() {
        var elements = document.querySelectorAll('[data-i18n]');

        elements.forEach(function(element) {
            var key = element.getAttribute('data-i18n');
            if (key && window.i18n && window.i18n.t) {
                element.textContent = window.i18n.t(key);
            }
        });
    }

    function init() {
        initializeFilters();
        initializePagination();
        initializeForms();
        initializeI18n();

        var filterForm = document.querySelector('.admin-filters');
        if (filterForm) {
            var formData = new FormData(filterForm);
            state.currentFilters = Object.fromEntries(formData.entries());
        }

        var urlParams = new URLSearchParams(window.location.search);
        var page = urlParams.get('page');
        if (page) {
            state.currentPage = parseInt(page);
        }

        console.log('Admin console initialized');
    }

    function initialize() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }

    window.AdminConsole = {
        showSkeleton: showSkeleton,
        hideSkeleton: hideSkeleton,
        showAlert: showAlert,
        refreshData: refreshData,
        formatNumber: formatNumber,
        formatCurrency: formatCurrency,
        formatDate: formatDate,
    };

    initialize();
})();
