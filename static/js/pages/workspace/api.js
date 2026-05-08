// @MX:ANCHOR: [AUTO] API client for all workspace endpoints with error handling and retry logic
// @MX:REASON: Single source of truth for all API calls from workspace to backend

// SPEC-05: API Error class for different error types
class APIError extends Error {
  constructor(status, statusText, data = {}) {
    super(statusText);
    this.status = status;
    this.statusText = statusText;
    this.code = data.code || 'unknown';
    this.message = data.message || statusText;
    this.details = data;
    this.retryable = this.isRetryable(status);
  }

  isRetryable(status) {
    // SPEC-05: Retryable errors: 429, 5xx, network errors
    return status === 429 || status >= 500 || status === 'NETWORK_ERROR';
  }

  getUserMessage() {
    // Return user-friendly error messages
    const errorMessages = {
      authRequired: 'workspace.errors.authRequired',
      permissionDenied: 'workspace.errors.permissionDenied',
      notFound: 'workspace.errors.notFound',
      conflict: 'workspace.errors.conflict',
      validationError: 'workspace.errors.validationError',
      quotaExceeded: 'workspace.errors.quotaExceeded',
      serverError: 'workspace.errors.serverError',
      networkError: 'workspace.errors.networkError',
      insufficientEvidence: 'workspace.errors.insufficientEvidence',
      licenseBlocked: 'workspace.errors.licenseBlocked',
      celeryTaskFailed: 'workspace.errors.celeryTaskFailed'
    };

    return errorMessages[this.code] || 'workspace.errors.unknown';
  }
}

class WorkspaceAPI {
  constructor(baseUrl = '/api/sessions') {
    this.baseUrl = baseUrl;
    this.retryConfig = {
      maxRetries: 3,
      retryDelay: 1000,
      backoffMultiplier: 2
    };
  }

  async getSession(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}`);
  }

  async getMessages(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/messages`);
  }

  async sendMessage(sessionId, content) {
    return this.request(`${this.baseUrl}/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
  }

  async uploadSketch(sessionId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`${this.baseUrl}/${sessionId}/sketches`, {
      method: 'POST',
      body: formData
    });
  }

  async searchReferences(sessionId, query, filters = {}) {
    return this.request(`${this.baseUrl}/${sessionId}/references/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, filters })
    });
  }

  async getAbstractionRules(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/abstraction-rules`);
  }

  async generateDesign(sessionId, params) {
    return this.request(`${this.baseUrl}/${sessionId}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
  }

  async decideConcept(sessionId, conceptId, decision) {
    return this.request(`${this.baseUrl}/${sessionId}/concepts/${conceptId}/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision })
    });
  }

  async getSpecDocument(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/spec`);
  }

  async getGenerationResults(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/generations`);
  }

  async saveSpecMemo(sessionId, sectionId, memo) {
    return this.request(`${this.baseUrl}/${sessionId}/spec/sections/${sectionId}/memo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memo })
    });
  }

  async request(url, options = {}) {
    let retries = 0;
    let delay = this.retryConfig.retryDelay;

    while (retries <= this.retryConfig.maxRetries) {
      try {
        const response = await fetch(url, options);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new APIError(response.status, response.statusText, errorData);
        }

        const data = await response.json();

        // SPEC-05-API: All responses include current_step, mode, evidence_refs, is_hypothesis, decision_required, next_actions
        return this.normalizeResponse(data);
      } catch (error) {
        if (retries === this.retryConfig.maxRetries) {
          throw this.handleError(error);
        }

        console.warn(`Request failed, retrying (${retries + 1}/${this.retryConfig.maxRetries}):`, error);
        await this.delay(delay);
        delay *= this.retryConfig.backoffMultiplier;
        retries++;
      }
    }
  }

  normalizeResponse(data) {
    // Ensure all SPEC-05-API required fields are present
    return {
      current_step: data.current_step || null,
      mode: data.mode || 'standard',
      evidence_refs: data.evidence_refs || [],
      is_hypothesis: data.is_hypothesis || false,
      decision_required: data.decision_required || false,
      next_actions: data.next_actions || [],
      ...data
    };
  }

  handleError(error) {
    if (error instanceof APIError) {
      return error;
    }

    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return new APIError('NETWORK_ERROR', 'Network connection failed', {
        code: 'networkError',
        message: 'Unable to connect to the server. Please check your internet connection.',
        retryable: true
      });
    }

    return error;
  }

  // SPEC-05: Handle HTTP errors differently: 401/403/404/409/422/429/5xx
  getErrorType(status) {
    if (status === 401) return 'authRequired';
    if (status === 403) return 'permissionDenied';
    if (status === 404) return 'notFound';
    if (status === 409) return 'conflict';
    if (status === 422) return 'validationError';
    if (status === 429) return 'quotaExceeded';
    if (status >= 500) return 'serverError';
    return 'unknown';
  }

  async getSketch(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/sketches/latest`);
  }

  async getSketchInterpretation(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/sketches/interpretation`);
  }

  async executeSketchAction(sessionId, action, params = {}) {
    return this.request(`${this.baseUrl}/${sessionId}/sketches/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, params })
    });
  }

  async getEvidence(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/evidence`);
  }

  async getReferences(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/references`);
  }

  async applyReferenceStyle(sessionId, referenceId) {
    return this.request(`${this.baseUrl}/${sessionId}/references/${referenceId}/apply`, {
      method: 'POST'
    });
  }

  async getDecisionCandidates(sessionId) {
    return this.request(`${this.baseUrl}/${sessionId}/concepts`);
  }

  async selectGeneration(sessionId, generationId) {
    return this.request(`${this.baseUrl}/${sessionId}/generations/${generationId}/select`, {
      method: 'POST'
    });
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export { WorkspaceAPI };
