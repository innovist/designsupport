// @MX:ANCHOR: [AUTO] Spec Builder board for viewing and annotating spec documents
// @MX:REASON: Central spec viewer with evidence/decision log citation links

class SpecBuilderBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.container = null;
    this.tocContainer = null;
    this.contentContainer = null;
    this.currentSection = null;
  }

  async initialize() {
    this.container = document.getElementById('spec-builder');
    this.tocContainer = document.getElementById('spec-toc');
    this.contentContainer = document.getElementById('spec-content');
    this.setupEventListeners();
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('spec-content', 'document');

      const specData = await this.workspace.api.getSpecDocument(this.workspace.state.sessionId);
      this.workspace.state.set('boards.spec', specData);

      this.renderTOC(specData.sections);
      this.renderContent(specData);
    } catch (error) {
      console.error('Failed to load spec document:', error);
      this.workspace.emptyState.showEmptyState('spec', 'noSpec', this.container);
    } finally {
      this.workspace.skeleton.hideSkeleton('spec-content');
    }
  }

  setupEventListeners() {
    const expandBtn = document.getElementById('spec-expand-rejected');
    expandBtn?.addEventListener('click', () => this.toggleRejectedConcepts());
  }

  renderTOC(sections) {
    if (!this.tocContainer) return;
    this.tocContainer.innerHTML = '';

    if (!sections || sections.length === 0) {
      this.tocContainer.innerHTML = '<p class="empty-state">No sections</p>';
      return;
    }

    const ul = document.createElement('ul');
    ul.className = 'spec-toc-list';

    sections.forEach(section => {
      const li = document.createElement('li');
      li.className = 'spec-toc-item';

      const link = document.createElement('a');
      link.href = `#section-${section.id}`;
      link.textContent = section.title;
      link.className = 'spec-toc-link';
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToSection(section.id);
      });

      li.appendChild(link);
      ul.appendChild(li);
    });

    this.tocContainer.appendChild(ul);
  }

  renderContent(specData) {
    if (!this.contentContainer) return;
    this.contentContainer.innerHTML = '';

    if (!specData || !specData.sections) {
      this.contentContainer.innerHTML = '<p class="empty-state">No spec content available</p>';
      return;
    }

    // Version and approval status
    const header = this.createSpecHeader(specData);
    this.contentContainer.appendChild(header);

    // Sections
    specData.sections.forEach(section => {
      const sectionDiv = this.createSection(section);
      this.contentContainer.appendChild(sectionDiv);
    });

    // Rejected/Held concepts (always visible, expandable)
    if (specData.rejected_concepts && specData.rejected_concepts.length > 0) {
      const rejectedDiv = this.createRejectedConcepts(specData.rejected_concepts);
      this.contentContainer.appendChild(rejectedDiv);
    }
  }

  createSpecHeader(specData) {
    const header = document.createElement('div');
    header.className = 'spec-header';

    const version = document.createElement('div');
    version.className = 'spec-version';
    version.textContent = `Version: ${specData.version || '1.0.0'}`;
    header.appendChild(version);

    const approvalStatus = document.createElement('div');
    approvalStatus.className = 'spec-approval-status';
    approvalStatus.textContent = specData.approved ? '✓ Approved' : 'Pending Review';
    approvalStatus.classList.add(specData.approved ? 'approved' : 'pending');
    header.appendChild(approvalStatus);

    return header;
  }

  createSection(section) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'spec-section';
    sectionDiv.id = `section-${section.id}`;

    const title = document.createElement('h3');
    title.className = 'spec-section-title';
    title.textContent = section.title;
    sectionDiv.appendChild(title);

    // Main content (read-only)
    const content = document.createElement('div');
    content.className = 'spec-section-content';
    content.innerHTML = section.content || '';
    sectionDiv.appendChild(content);

    // Citation links to Evidence Board
    if (section.evidence_refs && section.evidence_refs.length > 0) {
      const citationsDiv = this.createCitations(section.evidence_refs);
      sectionDiv.appendChild(citationsDiv);
    }

    // Decision log links
    if (section.decision_log_refs && section.decision_log_refs.length > 0) {
      const decisionsDiv = this.createDecisionLogLinks(section.decision_log_refs);
      sectionDiv.appendChild(decisionsDiv);
    }

    // Memo/annotation area (editable)
    const memoDiv = this.createMemoArea(section);
    sectionDiv.appendChild(memoDiv);

    return sectionDiv;
  }

  createCitations(evidenceRefs) {
    const container = document.createElement('div');
    container.className = 'spec-citations';

    const label = document.createElement('div');
    label.className = 'spec-citations-label';
    label.textContent = window.t('workspace.boards.spec.evidenceReferences');
    container.appendChild(label);

    evidenceRefs.forEach(ref => {
      const link = document.createElement('a');
      link.href = `#evidence-${ref.id}`;
      link.className = 'spec-citation-link';
      link.textContent = `📎 ${ref.title || ref.id}`;
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToEvidence(ref.id);
      });
      container.appendChild(link);
    });

    return container;
  }

  createDecisionLogLinks(decisionRefs) {
    const container = document.createElement('div');
    container.className = 'spec-decisions';

    const label = document.createElement('div');
    label.className = 'spec-decisions-label';
    label.textContent = window.t('workspace.boards.spec.decisionLog');
    container.appendChild(label);

    decisionRefs.forEach(ref => {
      const link = document.createElement('a');
      link.href = `#decision-${ref.id}`;
      link.className = 'spec-decision-link';
      link.textContent = `📋 ${ref.summary || ref.id}`;
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToDecision(ref.id);
      });
      container.appendChild(link);
    });

    return container;
  }

  createMemoArea(section) {
    const memoDiv = document.createElement('div');
    memoDiv.className = 'spec-memo-area';

    const label = document.createElement('label');
    label.className = 'spec-memo-label';
    label.textContent = window.t('workspace.boards.spec.memoLabel');
    label.htmlFor = `memo-${section.id}`;
    memoDiv.appendChild(label);

    const textarea = document.createElement('textarea');
    textarea.id = `memo-${section.id}`;
    textarea.className = 'spec-memo-textarea';
    textarea.value = section.memo || '';
    textarea.placeholder = window.t('workspace.boards.spec.memoPlaceholder');

    textarea.addEventListener('blur', () => this.saveMemo(section.id, textarea.value));

    memoDiv.appendChild(textarea);

    return memoDiv;
  }

  createRejectedConcepts(concepts) {
    const container = document.createElement('div');
    container.className = 'spec-rejected-concepts';

    const header = document.createElement('div');
    header.className = 'spec-rejected-header';

    const title = document.createElement('h4');
    title.textContent = window.t('workspace.boards.spec.rejectedConcepts');
    header.appendChild(title);

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn btn-sm btn-outline';
    toggleBtn.textContent = window.t('workspace.boards.spec.toggleExpand');
    toggleBtn.addEventListener('click', () => this.toggleRejectedConcepts());
    header.appendChild(toggleBtn);

    container.appendChild(header);

    const content = document.createElement('div');
    content.className = 'spec-rejected-content collapsed';

    concepts.forEach(concept => {
      const conceptDiv = document.createElement('div');
      conceptDiv.className = 'spec-rejected-item';

      const reason = document.createElement('div');
      reason.className = 'spec-rejected-reason';
      reason.textContent = `Reason: ${concept.rejection_reason || 'Not specified'}`;
      conceptDiv.appendChild(reason);

      const summary = document.createElement('div');
      summary.className = 'spec-rejected-summary';
      summary.textContent = concept.summary || concept.description || '';
      conceptDiv.appendChild(summary);

      content.appendChild(conceptDiv);
    });

    container.appendChild(content);

    return container;
  }

  async saveMemo(sectionId, memoContent) {
    try {
      await this.workspace.api.saveSpecMemo(
        this.workspace.state.sessionId,
        sectionId,
        memoContent
      );
    } catch (error) {
      console.error('Failed to save memo:', error);
      // Show error notification
      this.workspace.notifications.show(window.t('workspace.boards.spec.memoSaveFailed'), 'error');
    }
  }

  navigateToSection(sectionId) {
    const sectionElement = document.getElementById(`section-${sectionId}`);
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  navigateToEvidence() {
    this.workspace.boardManager.switchBoard('evidence');
  }

  navigateToDecision() {
    this.workspace.boardManager.switchBoard('decision');
  }

  toggleRejectedConcepts() {
    const content = this.container.querySelector('.spec-rejected-content');
    if (content) {
      content.classList.toggle('collapsed');
      content.classList.toggle('expanded');
    }
  }
}

export { SpecBuilderBoard };
