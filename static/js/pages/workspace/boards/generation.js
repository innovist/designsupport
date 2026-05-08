class GenerationBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.container = null;
  }

  async initialize() {
    this.container = document.getElementById('generation-results');
    this.setupEventListeners();
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('generation-results', 'image-grid');
      
      const results = await this.workspace.api.getGenerationResults(this.workspace.state.sessionId);
      this.workspace.state.set('boards.generation.results', results);
      
      this.renderResults(results);
    } catch (error) {
      console.error('Failed to load generation results:', error);
      this.workspace.emptyState.showEmptyState('generation', 'modelFailure', this.container);
    } finally {
      this.workspace.skeleton.hideSkeleton('generation-results');
    }
  }

  setupEventListeners() {
    const comparisonBtn = document.getElementById('generation-comparison');
    comparisonBtn?.addEventListener('click', () => this.showComparison());
  }

  renderResults(results) {
    if (!this.container) return;
    this.container.innerHTML = '';

    if (!results || results.length === 0) {
      this.container.innerHTML = '<p class="empty-state">No generation results</p>';
      return;
    }

    // Group by kind
    const grouped = this.groupByKind(results);

    Object.entries(grouped).forEach(([kind, items]) => {
      const section = this.createKindSection(kind, items);
      this.container.appendChild(section);
    });
  }

  groupByKind(results) {
    return results.reduce((acc, result) => {
      const kind = result.kind || 'unknown';
      if (!acc[kind]) acc[kind] = [];
      acc[kind].push(result);
      return acc;
    }, {});
  }

  createKindSection(kind, items) {
    const section = document.createElement('div');
    section.className = 'generation-section';

    const header = document.createElement('h3');
    header.textContent = window.t(`workspace.boards.generation.kinds.${kind}`);
    section.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'generation-results';

    items.forEach(item => {
      const card = this.createGenerationCard(item);
      grid.appendChild(card);
    });

    section.appendChild(grid);
    return section;
  }

  createGenerationCard(generation) {
    const card = document.createElement('div');
    card.className = 'generation-card';

    const imageDiv = document.createElement('div');
    imageDiv.className = 'generation-image';

    const img = document.createElement('img');
    img.src = generation.url;
    img.alt = generation.prompt || 'Generated image';
    imageDiv.appendChild(img);

    // AI Generated watermark with design token
    const watermark = document.createElement('div');
    watermark.className = 'ai-generated-badge';
    watermark.textContent = '✨ ' + window.t('workspace.boards.generation.aiGenerated');
    watermark.style.cssText = `
      position: absolute;
      top: 8px;
      right: 8px;
      background: var(--card-gen-border, #4CAF50);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: var(--font-xs, 0.75rem);
      font-weight: 600;
      z-index: 1;
    `;
    imageDiv.appendChild(watermark);

    card.appendChild(imageDiv);

    const meta = document.createElement('div');
    meta.className = 'generation-meta';

    // Kind badge
    const kind = document.createElement('span');
    kind.className = 'generation-kind';
    kind.textContent = window.t(`workspace.boards.generation.kinds.${generation.kind}`);
    meta.appendChild(kind);

    // Parent sketch link
    if (generation.parent_sketch_id) {
      const parentLink = document.createElement('a');
      parentLink.className = 'parent-sketch-link';
      parentLink.textContent = 'View parent sketch →';
      parentLink.href = `#sketch-${generation.parent_sketch_id}`;
      parentLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToSketch(generation.parent_sketch_id);
      });
      meta.appendChild(parentLink);
    }

    // Model policy key with enhanced styling
    if (generation.model_policy_key) {
      const policy = document.createElement('div');
      policy.className = 'model-policy-badge';
      policy.textContent = `🤖 ${generation.model_policy_key}`;
      policy.style.cssText = `
        display: inline-block;
        background: var(--card-gen-bg, #E8F5E9);
        color: var(--card-gen-border, #4CAF50);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: var(--font-xs, 0.75rem);
        font-weight: 500;
        margin-top: 4px;
      `;
      meta.appendChild(policy);
    }

    card.appendChild(meta);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'card-actions';
    actions.style.padding = 'var(--spacing-sm)';

    const selectBtn = document.createElement('button');
    selectBtn.className = 'btn btn-sm btn-primary';
    selectBtn.textContent = window.t('workspace.boards.generation.select');
    selectBtn.addEventListener('click', () => this.selectGeneration(generation));
    actions.appendChild(selectBtn);

    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'btn btn-sm btn-secondary';
    downloadBtn.textContent = window.t('workspace.boards.generation.download');
    downloadBtn.addEventListener('click', () => this.downloadGeneration(generation));
    actions.appendChild(downloadBtn);

    card.appendChild(actions);

    return card;
  }

  navigateToSketch() {
    this.workspace.boardManager.switchBoard('sketch');
  }

  async selectGeneration(generation) {
    try {
      await this.workspace.api.selectGeneration(
        this.workspace.state.sessionId,
        generation.id
      );
    } catch (error) {
      console.error('Failed to select generation:', error);
    }
  }

  async downloadGeneration(generation) {
    try {
      const response = await fetch(generation.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `generation_${generation.id}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  }

  showComparison() {
    // TODO: Implement comparison view
  }
}

export { GenerationBoard };
