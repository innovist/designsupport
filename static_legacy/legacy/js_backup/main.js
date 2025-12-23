// Main application logic

// DOM elements
const elements = {
    // Navigation
    navLinks: document.querySelectorAll('.nav-link'),

    // Trend Analysis
    trendKeywords: document.getElementById('trend-keywords'),
    timeRange: document.getElementById('time-range'),
    analyzeTrendsBtn: document.getElementById('analyze-trends'),
    trendResults: document.getElementById('trend-results'),

    // Image Generation
    designPrompt: document.getElementById('design-prompt'),
    garmentType: document.getElementById('garment-type'),
    style: document.getElementById('style'),
    colorScheme: document.getElementById('color-scheme'),
    fabricType: document.getElementById('fabric-type'),
    quality: document.getElementById('quality'),
    numVariations: document.getElementById('num-variations'),
    referenceImage: document.getElementById('reference-image'),
    generateDesignBtn: document.getElementById('generate-design'),
    generationResults: document.getElementById('generation-results'),

    // Blueprint Generation
    bpGarmentType: document.getElementById('bp-garment-type'),
    bpDesign: document.getElementById('bp-design'),
    sizeSystem: document.getElementById('size-system'),
    size: document.getElementById('size'),
    includeInstructions: document.getElementById('include-instructions'),
    includeSeam: document.getElementById('include-seam'),
    generateBlueprintBtn: document.getElementById('generate-blueprint'),
    blueprintResults: document.getElementById('blueprint-results'),

    // Crawler
    sourceCheckboxes: document.querySelectorAll('input[name="sources"]'),
    crawlerKeywords: document.getElementById('crawler-keywords'),
    maxItems: document.getElementById('max-items'),
    startCrawlingBtn: document.getElementById('start-crawling'),
    crawlerResults: document.getElementById('crawler-results')
};

let crawlJobId = null;
let crawlStatusInterval = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkServerHealth();
});

// Setup event listeners
function setupEventListeners() {
    // Navigation
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('href').substring(1);
            uiManager.switchSection(sectionId);
        });
    });

    // Trend Analysis
    elements.analyzeTrendsBtn.addEventListener('click', handleAnalyzeTrends);

    // Image Generation
    elements.generateDesignBtn.addEventListener('click', handleGenerateDesign);

    // Blueprint Generation
    elements.generateBlueprintBtn.addEventListener('click', handleGenerateBlueprint);

    // Crawler
    elements.startCrawlingBtn.addEventListener('click', handleStartCrawling);
}

// Helper function for i18n
const _t = (key, params = {}) => window.t ? window.t(key, params) : key;

// Check server health
async function checkServerHealth() {
    try {
        await fashionAPI.healthCheck();
    } catch (error) {
        uiManager.showError(_t('errors.serverError'));
    }
}

// ===== Trend Analysis Handlers =====

async function handleAnalyzeTrends() {
    const keywords = elements.trendKeywords.value
        .split(',')
        .map(k => k.trim())
        .filter(k => k);

    if (keywords.length === 0) {
        uiManager.showWarning(_t('trendAnalysis.notifications.enterKeywords'));
        return;
    }

    const timeRange = elements.timeRange.value;

    try {
        uiManager.showLoading(_t('ui.analyzing'));
        const result = await fashionAPI.analyzeTrends(keywords, timeRange);
        uiManager.displayTrendResults(result.data, 'trend-results');
        uiManager.showSuccess(_t('trendAnalysis.notifications.analysisComplete'));
    } catch (error) {
        uiManager.showError(_t('trendAnalysis.notifications.analysisFailed', { error: error.message }));
    } finally {
        uiManager.hideLoading();
    }
}

// ===== Image Generation Handlers =====

async function handleGenerateDesign() {
    const prompt = elements.designPrompt.value.trim();
    if (!prompt) {
        uiManager.showWarning(_t('imageGeneration.notifications.enterPrompt'));
        return;
    }

    const requestData = {
        prompt: prompt,
        garment_type: elements.garmentType.value,
        style: elements.style.value,
        color_scheme: elements.colorScheme.value || null,
        fabric_type: elements.fabricType.value || null,
        quality: elements.quality.value,
        num_variations: parseInt(elements.numVariations.value)
    };

    // Handle reference image if provided
    if (elements.referenceImage.files.length > 0) {
        uiManager.showWarning(_t('imageGeneration.notifications.referenceImageUpload'));
    }

    try {
        uiManager.showLoading(_t('ui.generating'));
        const result = await fashionAPI.generateFashionDesign(requestData);
        uiManager.displayImageResults(result.data.images, 'generation-results');
        uiManager.showSuccess(_t('imageGeneration.notifications.generationComplete'));
    } catch (error) {
        uiManager.showError(_t('imageGeneration.notifications.generationFailed', { error: error.message }));
    } finally {
        uiManager.hideLoading();
    }
}

// ===== Blueprint Generation Handlers =====

async function handleGenerateBlueprint() {
    const design = elements.bpDesign.value.trim();
    if (!design) {
        uiManager.showWarning(_t('blueprint.notifications.enterDesign'));
        return;
    }

    const requestData = {
        garment_type: elements.bpGarmentType.value,
        design_description: design,
        size_system: elements.sizeSystem.value,
        size: elements.size.value,
        include_instructions: elements.includeInstructions.checked,
        include_seam_allowance: elements.includeSeam.checked,
        seam_allowance_width: 1.5
    };

    try {
        uiManager.showLoading(_t('ui.generating'));
        const result = await fashionAPI.generateBlueprint(requestData);
        uiManager.displayBlueprintResults(result.data, 'blueprint-results');
        uiManager.showSuccess(_t('blueprint.notifications.generationComplete'));
    } catch (error) {
        uiManager.showError(_t('blueprint.notifications.generationFailed', { error: error.message }));
    } finally {
        uiManager.hideLoading();
    }
}

// ===== Crawler Handlers =====

async function handleStartCrawling() {
    const sources = Array.from(elements.sourceCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    if (sources.length === 0) {
        uiManager.showWarning(_t('crawler.notifications.selectSources'));
        return;
    }

    const keywords = elements.crawlerKeywords.value
        .split(',')
        .map(k => k.trim())
        .filter(k => k);

    if (keywords.length === 0) {
        uiManager.showWarning(_t('crawler.notifications.enterKeywords'));
        return;
    }

    const maxItems = parseInt(elements.maxItems.value);

    try {
        uiManager.showLoading(_t('ui.collecting'));
        const result = await fashionAPI.startCrawling(sources, keywords, maxItems);
        crawlJobId = result.data.job_id;
        uiManager.showSuccess(_t('crawler.notifications.started'));

        // Start polling for status
        startStatusPolling();

        // Update button
        elements.startCrawlingBtn.textContent = _t('ui.collecting');
        elements.startCrawlingBtn.disabled = true;
    } catch (error) {
        uiManager.showError(_t('crawler.notifications.startFailed', { error: error.message }));
        uiManager.hideLoading();
    }
}

function startStatusPolling() {
    if (crawlStatusInterval) {
        clearInterval(crawlStatusInterval);
    }

    crawlStatusInterval = setInterval(async () => {
        try {
            const status = await fashionAPI.getCrawlingStatus(crawlJobId);
            uiManager.displayCrawlStatus(status.data, 'crawler-results');

            if (status.data.status === 'completed') {
                clearInterval(crawlStatusInterval);
                crawlStatusInterval = null;

                // Get results
                const results = await fashionAPI.getCrawlingResults(crawlJobId);
                uiManager.displayCrawledItems(results.data.items, 'crawler-results');

                // Reset button
                elements.startCrawlingBtn.textContent = _t('crawler.start');
                elements.startCrawlingBtn.disabled = false;

                uiManager.showSuccess(_t('crawler.notifications.completed'));
            } else if (status.data.status === 'failed') {
                clearInterval(crawlStatusInterval);
                crawlStatusInterval = null;

                // Reset button
                elements.startCrawlingBtn.textContent = _t('crawler.start');
                elements.startCrawlingBtn.disabled = false;

                uiManager.showError(_t('crawler.notifications.failed'));
            }
        } catch (error) {
            console.error('Status polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (crawlStatusInterval) {
        clearInterval(crawlStatusInterval);
    }
});