/**
 * Settings management for Fashion AI Generator
 * Handles API key encryption, storage, and configuration
 */

class SettingsManager {
    constructor() {
        this.encryptionKey = this.generateEncryptionKey();
        this.storageKey = 'fashion_ai_settings';
        this.settings = this.loadSettings();
        this.initializeEventListeners();
    }

    // Generate encryption key from device fingerprint
    generateEncryptionKey() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
        const fingerprint = canvas.toDataURL() + navigator.userAgent + screen.width + screen.height;
        return fingerprint.slice(0, 32); // Use first 32 chars as key
    }

    // Encrypt data using AES
    encrypt(data) {
        return CryptoJS.AES.encrypt(JSON.stringify(data), this.encryptionKey).toString();
    }

    // Decrypt data using AES
    decrypt(encryptedData) {
        try {
            const bytes = CryptoJS.AES.decrypt(encryptedData, this.encryptionKey);
            return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
        } catch (e) {
            console.error('Decryption failed:', e);
            return null;
        }
    }

    // Load settings from localStorage
    loadSettings() {
        const encrypted = localStorage.getItem(this.storageKey);
        if (!encrypted) {
            return this.getDefaultSettings();
        }
        const decrypted = this.decrypt(encrypted);
        return decrypted || this.getDefaultSettings();
    }

    // Get default settings
    getDefaultSettings() {
        return {
            apiKeys: {
                gemini: '',
                glm: '',
                zimage: '',
                seedream: '',
                nanoBanana: ''
            },
            system: {
                maxConcurrentRequests: 5,
                requestTimeout: 300,
                defaultLanguage: 'ko',
                defaultQuality: 'high',
                autoSaveResults: true
            }
        };
    }

    // Save settings to localStorage
    saveSettings() {
        const encrypted = this.encrypt(this.settings);
        localStorage.setItem(this.storageKey, encrypted);
        this.updateApiStatus();
        if (window.uiManager) {
            const _t = window.t || ((k) => k);
            uiManager.showSuccess(_t('settings.notifications.saved'));
        }
    }

    // Get API key
    getApiKey(service) {
        return this.settings.apiKeys[service] || '';
    }

    // Set API key
    setApiKey(service, key) {
        this.settings.apiKeys[service] = key;
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // API key visibility toggle
        document.querySelectorAll('.btn-toggle-visibility').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = e.target.dataset.target;
                const input = document.getElementById(targetId);
                if (input.type === 'password') {
                    input.type = 'text';
                    e.target.textContent = '🙈';
                } else {
                    input.type = 'password';
                    e.target.textContent = '👁️';
                }
            });
        });

        // API keys form submission
        document.getElementById('api-keys-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveApiKeys();
        });

        // System settings form submission
        document.getElementById('system-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSystemSettings();
        });

        // Test API connection
        document.getElementById('test-api-connection').addEventListener('click', () => {
            this.testApiConnections();
        });

        // Reset keys
        document.getElementById('reset-keys').addEventListener('click', () => {
            if (confirm('모든 API 키를 초기화하시겠습니까?')) {
                this.resetApiKeys();
            }
        });

        // Reset system settings
        document.getElementById('reset-system').addEventListener('click', () => {
            if (confirm('시스템 설정을 기본값으로 되돌리시겠습니까?')) {
                this.resetSystemSettings();
            }
        });

        // Export settings
        document.getElementById('export-settings').addEventListener('click', () => {
            this.exportSettings();
        });

        // Import settings
        document.getElementById('import-settings-btn').addEventListener('click', () => {
            document.getElementById('import-settings').click();
        });

        document.getElementById('import-settings').addEventListener('change', (e) => {
            this.importSettings(e.target.files[0]);
        });
    }

    // Switch tabs
    switchTab(tabName) {
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');
    }

    // Save API keys from form
    saveApiKeys() {
        const services = ['gemini', 'glm', 'zimage', 'seedream', 'nanoBanana'];
        services.forEach(service => {
            const input = document.getElementById(`${service}-api-key`);
            if (input) {
                this.setApiKey(service, input.value);
            }
        });
        this.saveSettings();
    }

    // Save system settings from form
    saveSystemSettings() {
        this.settings.system = {
            maxConcurrentRequests: parseInt(document.getElementById('max-concurrent-requests').value),
            requestTimeout: parseInt(document.getElementById('request-timeout').value),
            defaultLanguage: document.getElementById('default-language').value,
            defaultQuality: document.getElementById('default-quality').value,
            autoSaveResults: document.getElementById('auto-save-results').checked
        };
        this.saveSettings();
    }

    // Load settings into form
    loadSettingsIntoForm() {
        // Load API keys
        const services = ['gemini', 'glm', 'zimage', 'seedream', 'nanoBanana'];
        services.forEach(service => {
            const input = document.getElementById(`${service}-api-key`);
            if (input && this.settings.apiKeys[service]) {
                input.value = this.settings.apiKeys[service];
            }
        });

        // Load system settings
        const sys = this.settings.system;
        document.getElementById('max-concurrent-requests').value = sys.maxConcurrentRequests;
        document.getElementById('request-timeout').value = sys.requestTimeout;
        document.getElementById('default-language').value = sys.defaultLanguage;
        document.getElementById('default-quality').value = sys.defaultQuality;
        document.getElementById('auto-save-results').checked = sys.autoSaveResults;
    }

    // Test API connections
    async testApiConnections() {
        const statusDiv = document.getElementById('connection-status');
        statusDiv.classList.remove('hidden');
        const _t = window.t || ((k) => k);

        const services = ['gemini', 'glm', 'zimage'];
        for (const service of services) {
            const statusIndicator = document.getElementById(`${service}-status`);
            const dot = statusIndicator.querySelector('.status-dot');
            const text = statusIndicator.querySelector('.status-text');

            dot.className = 'status-dot testing';
            text.textContent = _t('settings.status.testing');

            try {
                const result = await this.testSingleApi(service);
                if (result.success) {
                    dot.className = 'status-dot online';
                    text.textContent = _t('settings.status.online');
                } else {
                    dot.className = 'status-dot offline';
                    text.textContent = result.error;
                }
            } catch (e) {
                dot.className = 'status-dot offline';
                text.textContent = _t('settings.status.offline');
            }
        }
    }

    // Test single API connection
    async testSingleApi(service) {
        const apiKey = this.getApiKey(service);
        const _t = window.t || ((k) => k);
        if (!apiKey) {
            return { success: false, error: _t('settings.notifications.noApiKey') };
        }

        try {
            const response = await fetch('/api/v1/settings/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ service, api_key: apiKey })
            });

            const result = await response.json();
            return result;
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    // Reset API keys
    resetApiKeys() {
        this.settings.apiKeys = this.getDefaultSettings().apiKeys;
        this.saveSettings();
        document.querySelectorAll('.api-key-input').forEach(input => {
            input.value = '';
        });
        if (window.uiManager) {
            const _t = window.t || ((k) => k);
            uiManager.showNotification(_t('settings.notifications.reset'), 'info');
        }
    }

    // Reset system settings
    resetSystemSettings() {
        this.settings.system = this.getDefaultSettings().system;
        this.saveSettings();
        this.loadSettingsIntoForm();
        if (window.uiManager) {
            const _t = window.t || ((k) => k);
            uiManager.showNotification(_t('settings.notifications.reset'), 'info');
        }
    }

    // Export settings to file
    exportSettings() {
        const encrypted = this.encrypt(this.settings);
        const blob = new Blob([encrypted], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fashion-ai-settings-${new Date().toISOString().slice(0, 10)}.fashion`;
        a.click();
        URL.revokeObjectURL(url);
        if (window.uiManager) {
            const _t = window.t || ((k) => k);
            uiManager.showSuccess(_t('settings.notifications.exported'));
        }
    }

    // Import settings from file
    async importSettings(file) {
        if (!file) return;
        const _t = window.t || ((k) => k);

        try {
            const text = await file.text();
            const imported = this.decrypt(text);
            if (imported) {
                this.settings = imported;
                this.saveSettings();
                this.loadSettingsIntoForm();
                if (window.uiManager) {
                    uiManager.showSuccess(_t('settings.notifications.imported'));
                }
            } else {
                if (window.uiManager) {
                    uiManager.showError(_t('settings.notifications.decryptFailed'));
                }
            }
        } catch (e) {
            if (window.uiManager) {
                uiManager.showError(_t('settings.notifications.importFailed'));
            }
        }
    }

    // Update API status indicator in navbar
    updateApiStatus() {
        const statusIndicator = document.getElementById('api-status');
        if (!statusIndicator) return;

        const dot = statusIndicator.querySelector('.status-dot');
        const text = statusIndicator.querySelector('.status-text');
        const _t = window.t || ((k) => k);

        const hasRequiredKeys = this.getApiKey('gemini') && this.getApiKey('glm');
        if (hasRequiredKeys) {
            dot.className = 'status-dot online';
            text.textContent = _t('settings.status.configured');
        } else {
            dot.className = 'status-dot offline';
            text.textContent = _t('settings.status.notConfigured');
        }
    }

    // Check if API is configured
    isApiConfigured() {
        return this.getApiKey('gemini') && this.getApiKey('glm');
    }
}

// Initialize settings manager
const settingsManager = new SettingsManager();

// Load settings into form when page loads
document.addEventListener('DOMContentLoaded', () => {
    settingsManager.loadSettingsIntoForm();
    settingsManager.updateApiStatus();
});

// Export for use in other modules
window.SettingsManager = SettingsManager;
window.settingsManager = settingsManager;