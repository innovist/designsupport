// Internationalization (i18n) System

class I18nManager {
    constructor() {
        this.currentLanguage = 'ko';
        this.translations = {};
        this.fallbackLanguage = 'en';

        // Load translations based on browser language or saved preference
        this.init();
    }

    async init() {
        // Get saved language or browser language
        const savedLang = localStorage.getItem('fashion_ai_language');
        const browserLang = navigator.language || navigator.languages[0];

        // Map browser languages to supported languages
        const langMap = {
            'ko': 'ko',
            'ko-KR': 'ko',
            'en': 'en',
            'en-US': 'en',
            'en-GB': 'en',
            'zh': 'zh-CN',
            'zh-CN': 'zh-CN',
            'zh-TW': 'zh-TW',
            'zh-HK': 'zh-TW'
        };

        this.currentLanguage = langMap[savedLang] || langMap[browserLang] || 'ko';

        // Load translations
        await this.loadTranslations(this.currentLanguage);

        // Apply translations to the page
        this.applyTranslations();

        // Add language selector to page if not exists
        this.addLanguageSelector();
    }

    async loadTranslations(language) {
        try {
            const response = await fetch(`/static/i18n/${language}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load ${language} translations`);
            }
            this.translations[language] = await response.json();
        } catch (error) {
            console.error(`Error loading translations for ${language}:`, error);

            // Load fallback language if not already loaded
            if (language !== this.fallbackLanguage && !this.translations[this.fallbackLanguage]) {
                await this.loadTranslations(this.fallbackLanguage);
            }
        }
    }

    get(key, params = {}) {
        // Try to get translation in current language
        let translation = this.getNestedValue(this.translations[this.currentLanguage], key);

        // If not found, try fallback language
        if (!translation && this.currentLanguage !== this.fallbackLanguage) {
            translation = this.getNestedValue(this.translations[this.fallbackLanguage], key);
        }

        // If still not found, return key
        if (!translation) {
            return key;
        }

        // Replace parameters in translation
        if (typeof translation === 'string' && Object.keys(params).length > 0) {
            return this.interpolate(translation, params);
        }

        return translation;
    }

    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : null;
        }, obj);
    }

    interpolate(str, params) {
        return str.replace(/\{(\w+)\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }

    async setLanguage(language) {
        if (language === this.currentLanguage) return;

        // Load new language translations if not already loaded
        if (!this.translations[language]) {
            await this.loadTranslations(language);
        }

        this.currentLanguage = language;

        // Save preference
        localStorage.setItem('fashion_ai_language', language);

        // Apply translations
        this.applyTranslations();

        // Update language selector
        this.updateLanguageSelector();

        // Update HTML lang attribute
        document.documentElement.lang = language;

        // Trigger custom event
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language }
        }));
    }

    applyTranslations() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.get(key);

            if (translation) {
                element.textContent = translation;
            }
        });

        // Update placeholders with data-i18n-placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.get(key);

            if (translation) {
                element.placeholder = translation;
            }
        });

        // Update elements with data-i18n-html attribute (for HTML content)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            const translation = this.get(key);

            if (translation) {
                element.innerHTML = translation;
            }
        });

        // Update page title
        const titleKey = document.head.getAttribute('data-i18n-title');
        if (titleKey) {
            const titleTranslation = this.get(titleKey);
            if (titleTranslation) {
                document.title = titleTranslation;
            }
        }

        // Update form labels and options
        this.updateFormElements();
    }

    updateFormElements() {
        // Update labels
        document.querySelectorAll('label').forEach(label => {
            const forElement = document.getElementById(label.getAttribute('for'));
            if (forElement && forElement.hasAttribute('data-i18n')) {
                const key = forElement.getAttribute('data-i18n');
                const translation = this.get(key);
                if (translation && !label.querySelector('.translated-text')) {
                    const span = document.createElement('span');
                    span.className = 'translated-text';
                    span.textContent = translation;
                    label.innerHTML = '';
                    label.appendChild(span);
                }
            }
        });

        // Update select options
        document.querySelectorAll('select[data-i18n-options]').forEach(select => {
            const optionsKey = select.getAttribute('data-i18n-options');
            const options = this.get(optionsKey);

            if (options) {
                select.querySelectorAll('option').forEach(option => {
                    const value = option.value;
                    if (options[value]) {
                        option.textContent = options[value];
                    }
                });
            }
        });

        // Update buttons
        document.querySelectorAll('button[data-i18n]').forEach(button => {
            const key = button.getAttribute('data-i18n');
            const translation = this.get(key);
            if (translation) {
                // Keep icons if present
                const icon = button.querySelector('i, svg, .icon');
                if (icon) {
                    button.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            node.textContent = translation;
                        }
                    });
                } else {
                    button.textContent = translation;
                }
            }
        });
    }

    addLanguageSelector() {
        // Check for existing language selector (from HTML or previously created)
        const existingSelector = document.getElementById('language-select') ||
                                 document.getElementById('language-selector');

        if (existingSelector) {
            // Attach event listener to existing selector
            existingSelector.value = this.currentLanguage;
            existingSelector.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
            });
            return;
        }

        // Create new selector only if none exists
        const selector = document.createElement('select');
        selector.id = 'language-selector';
        selector.className = 'language-selector';
        selector.innerHTML = `
            <option value="ko" ${this.currentLanguage === 'ko' ? 'selected' : ''}>한국어</option>
            <option value="en" ${this.currentLanguage === 'en' ? 'selected' : ''}>English</option>
            <option value="zh-CN" ${this.currentLanguage === 'zh-CN' ? 'selected' : ''}>中文(简体)</option>
            <option value="zh-TW" ${this.currentLanguage === 'zh-TW' ? 'selected' : ''}>中文(繁體)</option>
        `;

        selector.addEventListener('change', (e) => {
            this.setLanguage(e.target.value);
        });

        // Add to nav-actions if exists
        const navActions = document.querySelector('.nav-actions');
        if (navActions) {
            const wrapper = document.createElement('div');
            wrapper.className = 'language-selector';
            wrapper.appendChild(selector);
            navActions.prepend(wrapper);
        }
    }

    updateLanguageSelector() {
        const selector = document.getElementById('language-select') ||
                         document.getElementById('language-selector');
        if (selector) {
            selector.value = this.currentLanguage;
        }
    }

    formatDate(date, format = 'short') {
        const formatKey = `dateFormats.${format}`;
        const formatString = this.get(formatKey) || 'YYYY-MM-DD';

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');

        // Simple format replacement (could use a library for more complex formatting)
        return formatString
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    formatNumber(number, options = {}) {
        const locale = this.getNumberLocale();
        return new Intl.NumberFormat(locale, options).format(number);
    }

    getNumberLocale() {
        const localeMap = {
            'ko': 'ko-KR',
            'en': 'en-US',
            'zh-CN': 'zh-CN',
            'zh-TW': 'zh-TW'
        };
        return localeMap[this.currentLanguage] || 'en-US';
    }

    getCurrency() {
        return this.get('currency') || { symbol: '$', code: 'USD' };
    }

    getSizeSystem() {
        // Get size system from preferences or default based on language
        const savedSystem = localStorage.getItem('fashion_ai_size_system');
        if (savedSystem) {
            return savedSystem;
        }

        const defaultSystems = {
            'ko': 'KS',
            'en': 'ASTM',
            'zh-CN': 'GB',
            'zh-TW': 'GB'
        };

        return defaultSystems[this.currentLanguage] || 'KS';
    }

    setSizeSystem(system) {
        localStorage.setItem('fashion_ai_size_system', system);
        window.dispatchEvent(new CustomEvent('sizeSystemChanged', {
            detail: { system }
        }));
    }
}

// Create global i18n manager instance
const i18n = new I18nManager();

// Helper function for easy translation
const t = (key, params) => i18n.get(key, params);

// Export for use in other modules
window.i18n = i18n;
window.t = t;