class EvidenceBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.container = null;
  }

  async initialize() {
    this.container = document.getElementById('evidence-cards');
    this.setupEventListeners();
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('evidence-cards', 'cards');
      
      const evidenceData = await this.workspace.api.getEvidence(this.workspace.state.sessionId);
      this.workspace.state.set('boards.evidence.insights', evidenceData.insights);
      
      this.renderEvidence(evidenceData.insights);
    } catch (error) {
      console.error('Failed to load evidence:', error);
      this.workspace.emptyState.showEmptyState('evidence', 'noTrendData', this.container);
    } finally {
      this.workspace.skeleton.hideSkeleton('evidence-cards');
    }
  }

  setupEventListeners() {
    const filterSelect = document.getElementById('evidence-filter');
    const sortSelect = document.getElementById('evidence-sort');

    filterSelect?.addEventListener('change', () => this.applyFilters());
    sortSelect?.addEventListener('change', () => this.applySort());
  }

  renderEvidence(insights) {
    if (!this.container) return;
    this.container.innerHTML = '';

    if (!insights || insights.length === 0) {
      this.workspace.emptyState.showEmptyState('evidence', 'noTrendData', this.container);
      return;
    }

    insights.forEach(insight => {
      const card = this.createEvidenceCard(insight);
      this.container.appendChild(card);
    });
  }

  createEvidenceCard(insight) {
    const card = document.createElement('div');
    card.className = 'evidence-card';
    card.setAttribute('tabindex', '0');

    const source = document.createElement('div');
    source.className = 'evidence-source';
    source.textContent = insight.source_url || 'Unknown source';
    card.appendChild(source);

    const content = document.createElement('p');
    content.className = 'evidence-content';
    content.textContent = insight.content || insight.summary;
    card.appendChild(content);

    const date = document.createElement('div');
    date.className = 'evidence-date';
    date.textContent = insight.publish_date || '';
    card.appendChild(date);

    const credibility = document.createElement('div');
    credibility.className = 'evidence-credibility';
    credibility.textContent = `Credibility: ${Math.round(insight.credibility_score * 100)}%`;
    card.appendChild(credibility);

    card.addEventListener('click', () => this.expandInsight(insight));
    card.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.expandInsight(insight);
    });

    return card;
  }

  expandInsight(_insight) {
    // TODO: Show modal with full insight details
  }

  applyFilters() {
    const filterValue = document.getElementById('evidence-filter')?.value;
    if (!filterValue) return;
    this.container.querySelectorAll('.evidence-card').forEach((card) => {
      const tags = card.dataset.tags?.split(',') || [];
      card.style.display = tags.some((t) => t.includes(filterValue)) ? '' : 'none';
    });
  }

  applySort() {
    const sortValue = document.getElementById('evidence-sort')?.value;
    if (!sortValue) return;
    const cards = [...this.container.querySelectorAll('.evidence-card')];
    cards.sort((a, b) => {
      if (sortValue === 'date') return new Date(b.dataset.date) - new Date(a.dataset.date);
      if (sortValue === 'confidence') return parseFloat(b.dataset.confidence || 0) - parseFloat(a.dataset.confidence || 0);
      return 0;
    });
    cards.forEach((card) => this.container.appendChild(card));
  }
}

export { EvidenceBoard };
