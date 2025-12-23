// API Client for Fashion AI Generator

class FashionAPI {
    constructor() {
        this.baseURL = '';
        this.headers = {
            'Content-Type': 'application/json'
        };
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // File upload
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);

        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        return data;
    }

    // ===== Trend Analysis APIs =====

    async analyzeTrends(keywords, timeRange = '7d') {
        return this.post('/api/v1/analysis/analyze-trends', {
            keywords: keywords,
            time_range: timeRange
        });
    }

    async analyzeFashionImage(imageFile) {
        return this.uploadFile('/api/v1/analysis/analyze-image', imageFile);
    }

    // ===== Image Generation APIs =====

    async generateFashionDesign(requestData) {
        return this.post('/api/v1/generation/fashion-design', requestData);
    }

    async generateFashionCollection(requestData) {
        return this.post('/api/v1/generation/collection', requestData);
    }

    async generateTechnicalSketch(requestData) {
        return this.post('/api/v1/generation/technical-sketch', requestData);
    }

    // ===== Blueprint APIs =====

    async generateBlueprint(requestData) {
        return this.post('/api/v1/blueprint/generate', requestData);
    }

    async exportBlueprintPDF(blueprintId) {
        return this.get(`/api/v1/blueprint/export/${blueprintId}`);
    }

    // ===== Crawler APIs =====

    async startCrawling(sources, keywords, maxItems = 100) {
        return this.post('/api/v1/crawler/start', {
            sources: sources,
            keywords: keywords,
            max_items: maxItems
        });
    }

    async getCrawlingStatus(jobId) {
        return this.get(`/api/v1/crawler/status/${jobId}`);
    }

    async getCrawlingResults(jobId) {
        return this.get(`/api/v1/crawler/results/${jobId}`);
    }

    // ===== Model Information APIs =====

    async getImageGenerationModels() {
        return this.get('/api/v1/models/image-generation');
    }

    async getTextGenerationModels() {
        return this.get('/api/v1/models/text-generation');
    }

    // ===== Utility APIs =====

    async healthCheck() {
        return this.get('/api/v1/health');
    }
}

// Create global API instance
const fashionAPI = new FashionAPI();