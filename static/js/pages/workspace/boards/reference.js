class ReferenceBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.clustersPanel = null;
    this.gridPanel = null;
    this.analysisPanel = null;
  }

  async initialize() {
    this.clustersPanel = document.getElementById('reference-clusters-content');
    this.gridPanel = document.getElementById('reference-grid-content');
    this.analysisPanel = document.getElementById('reference-analysis-content');
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('reference-clusters', 'list');
      this.workspace.skeleton.showSkeleton('reference-grid', 'image-grid');
      this.workspace.skeleton.showSkeleton('reference-analysis', 'text');
      
      const referenceData = await this.workspace.api.getReferences(this.workspace.state.sessionId);
      this.workspace.state.set('boards.reference.clusters', referenceData.clusters);
      this.workspace.state.set('boards.reference.grid', referenceData.grid);
      
      this.renderClusters(referenceData.clusters);
      this.renderGrid(referenceData.grid);
    } catch (error) {
      console.error('Failed to load references:', error);
      this.workspace.emptyState.showEmptyState('reference', 'noReferences', this.gridPanel);
    } finally {
      this.workspace.skeleton.hideSkeleton('reference-clusters');
      this.workspace.skeleton.hideSkeleton('reference-grid');
      this.workspace.skeleton.hideSkeleton('reference-analysis');
    }
  }

  renderClusters(clusters) {
    if (!this.clustersPanel) return;
    this.clustersPanel.innerHTML = '';

    if (!clusters || clusters.length === 0) {
      this.clustersPanel.innerHTML = '<p class="empty-state">No clusters</p>';
      return;
    }

    clusters.forEach(cluster => {
      const clusterDiv = document.createElement('div');
      clusterDiv.className = 'cluster-group';
      
      const title = document.createElement('h4');
      title.textContent = cluster.source;
      clusterDiv.appendChild(title);
      
      const count = document.createElement('span');
      count.className = 'cluster-count';
      count.textContent = `${cluster.count} items`;
      clusterDiv.appendChild(count);
      
      this.clustersPanel.appendChild(clusterDiv);
    });
  }

  renderGrid(references) {
    if (!this.gridPanel) return;
    this.gridPanel.innerHTML = '';

    if (!references || references.length === 0) {
      this.workspace.emptyState.showEmptyState('reference', 'noReferences', this.gridPanel);
      return;
    }

    references.forEach(ref => {
      const thumbnail = this.createReferenceThumbnail(ref);
      this.gridPanel.appendChild(thumbnail);
    });
  }

  createReferenceThumbnail(reference) {
    const thumbnail = document.createElement('div');
    thumbnail.className = 'reference-thumbnail';
    thumbnail.setAttribute('tabindex', '0');

    const img = document.createElement('img');
    img.src = reference.thumbnail_url || reference.url;
    img.alt = reference.title || 'Reference image';
    thumbnail.appendChild(img);

    // Category badge
    const category = document.createElement('span');
    category.className = 'category-badge';
    category.textContent = reference.category || 'Unknown';
    thumbnail.appendChild(category);

    // License risk badge
    if (reference.license_risk === 'high') {
      const risk = document.createElement('span');
      risk.className = 'license-risk';
      risk.textContent = '⚠️ High risk';
      thumbnail.appendChild(risk);
    }

    thumbnail.addEventListener('click', () => this.showAnalysis(reference));
    thumbnail.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.showAnalysis(reference);
    });

    return thumbnail;
  }

  showAnalysis(reference) {
    if (!this.analysisPanel) return;

    this.analysisPanel.innerHTML = '';

    // Image preview
    const img = document.createElement('img');
    img.src = reference.url;
    img.style.width = '100%';
    img.style.borderRadius = '6px';
    this.analysisPanel.appendChild(img);

    // Title
    const title = document.createElement('h4');
    title.textContent = reference.title || 'Untitled';
    this.analysisPanel.appendChild(title);

    // Similarity score
    if (reference.similarity_score) {
      const similarity = document.createElement('div');
      similarity.innerHTML = `<strong>Similarity:</strong> ${Math.round(reference.similarity_score * 100)}%`;
      this.analysisPanel.appendChild(similarity);
    }

    // License info
    if (reference.license) {
      const license = document.createElement('div');
      license.innerHTML = `<strong>License:</strong> ${reference.license}`;
      this.analysisPanel.appendChild(license);
    }

    // Risk warning
    if (reference.license_risk === 'high') {
      const warning = document.createElement('div');
      warning.className = 'error-state';
      warning.textContent = window.t('workspace.boards.reference.riskReason');
      this.analysisPanel.appendChild(warning);
    }

    // Direct apply button (disabled if high risk)
    const applyBtn = document.createElement('button');
    applyBtn.className = 'btn btn-primary';
    applyBtn.textContent = window.t('workspace.boards.reference.directApply');
    applyBtn.disabled = reference.license_risk === 'high';
    applyBtn.addEventListener('click', () => this.applyStyle(reference));
    this.analysisPanel.appendChild(applyBtn);
  }

  async applyStyle(reference) {
    try {
      await this.workspace.api.applyReferenceStyle(
        this.workspace.state.sessionId,
        reference.id
      );
    } catch (error) {
      console.error('Failed to apply style:', error);
    }
  }
}

export { ReferenceBoard };
