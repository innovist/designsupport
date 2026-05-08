class DecisionBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.candidatesContainer = null;
    this.logContainer = null;
  }

  async initialize() {
    this.candidatesContainer = document.getElementById('decision-candidates');
    this.logContainer = document.getElementById('decision-log');
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('decision-candidates', 'cards');
      
      const candidates = await this.workspace.api.getDecisionCandidates(this.workspace.state.sessionId);
      this.workspace.state.set('boards.decision.candidates', candidates);
      
      this.renderCandidates(candidates);
      this.renderDecisionLog();
    } catch (error) {
      console.error('Failed to load decision candidates:', error);
      this.workspace.emptyState.showEmptyState('decision', 'modelFailure', this.candidatesContainer);
    } finally {
      this.workspace.skeleton.hideSkeleton('decision-candidates');
    }
  }

  renderCandidates(candidates) {
    if (!this.candidatesContainer) return;
    this.candidatesContainer.innerHTML = '';

    if (!candidates || candidates.length === 0) {
      this.candidatesContainer.innerHTML = '<p class="empty-state">No candidates yet</p>';
      return;
    }

    candidates.forEach(candidate => {
      const card = this.createCandidateCard(candidate);
      this.candidatesContainer.appendChild(card);
    });
  }

  createCandidateCard(candidate) {
    const card = document.createElement('div');
    card.className = 'decision-card';
    if (candidate.status === 'selected') card.classList.add('selected');
    if (candidate.status === 'rejected') card.classList.add('rejected');

    // Image
    const imageDiv = document.createElement('div');
    imageDiv.className = 'decision-image';
    const img = document.createElement('img');
    img.src = candidate.thumbnail_url || candidate.url;
    img.alt = candidate.title || 'Concept candidate';
    imageDiv.appendChild(img);
    card.appendChild(imageDiv);

    // Scores
    const scores = document.createElement('div');
    scores.className = 'decision-scores';

    const creativity = this.createScoreItem(
      window.t('workspace.boards.decision.scores.creativity'),
      candidate.scores?.creativity || 0
    );
    scores.appendChild(creativity);

    const feasibility = this.createScoreItem(
      window.t('workspace.boards.decision.scores.feasibility'),
      candidate.scores?.feasibility || 0
    );
    scores.appendChild(feasibility);

    const marketFit = this.createScoreItem(
      window.t('workspace.boards.decision.scores.marketFit'),
      candidate.scores?.market_fit || 0
    );
    scores.appendChild(marketFit);

    card.appendChild(scores);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'decision-actions';

    const selectBtn = document.createElement('button');
    selectBtn.className = 'btn btn-sm btn-success';
    selectBtn.textContent = window.t('workspace.boards.decision.actions.select');
    selectBtn.disabled = candidate.status === 'selected';
    selectBtn.addEventListener('click', () => this.makeDecision(candidate.id, 'adopt'));
    actions.appendChild(selectBtn);

    const rejectBtn = document.createElement('button');
    rejectBtn.className = 'btn btn-sm btn-secondary';
    rejectBtn.textContent = window.t('workspace.boards.decision.actions.reject');
    rejectBtn.disabled = candidate.status === 'rejected';
    rejectBtn.addEventListener('click', () => this.makeDecision(candidate.id, 'discard'));
    actions.appendChild(rejectBtn);

    const revisionBtn = document.createElement('button');
    revisionBtn.className = 'btn btn-sm btn-outline';
    revisionBtn.textContent = window.t('workspace.boards.decision.actions.requestRevision');
    revisionBtn.addEventListener('click', () => this.makeDecision(candidate.id, 'explore_more'));
    actions.appendChild(revisionBtn);

    card.appendChild(actions);

    return card;
  }

  createScoreItem(label, score) {
    const item = document.createElement('div');
    item.className = 'decision-score';

    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    item.appendChild(labelSpan);

    const scoreSpan = document.createElement('span');
    scoreSpan.textContent = Math.round(score * 100) + '%';
    item.appendChild(scoreSpan);

    return item;
  }

  async makeDecision(candidateId, decision) {
    try {
      await this.workspace.api.decideConcept(
        this.workspace.state.sessionId,
        candidateId,
        decision
      );

      // Reload candidates
      await this.load();
    } catch (error) {
      console.error('Decision failed:', error);
    }
  }

  renderDecisionLog() {
    if (!this.logContainer) return;

    const log = this.workspace.state.get('boards.decision.log') || [];
    this.logContainer.innerHTML = '';

    if (log.length === 0) {
      this.logContainer.innerHTML = '<p class="empty-state">No decisions yet</p>';
      return;
    }

    log.forEach(entry => {
      const logEntry = document.createElement('div');
      logEntry.className = `log-entry ${entry.action}`;
      
      const timestamp = document.createElement('div');
      timestamp.className = 'log-timestamp';
      timestamp.textContent = new Date(entry.timestamp).toLocaleString();
      logEntry.appendChild(timestamp);

      const message = document.createElement('div');
      message.className = 'log-message';
      message.textContent = entry.message;
      logEntry.appendChild(message);

      this.logContainer.appendChild(logEntry);
    });
  }
}

export { DecisionBoard };
