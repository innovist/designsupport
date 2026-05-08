class AbstractionBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.container = null;
  }

  async initialize() {
    this.container = document.getElementById('abstraction-rules');
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('abstraction-rules', 'cards');
      
      const rules = await this.workspace.api.getAbstractionRules(this.workspace.state.sessionId);
      this.workspace.state.set('boards.abstraction.rules', rules);
      
      this.renderRules(rules);
    } catch (error) {
      console.error('Failed to load abstraction rules:', error);
      this.workspace.emptyState.showEmptyState('abstraction', 'modelFailure', this.container);
    } finally {
      this.workspace.skeleton.hideSkeleton('abstraction-rules');
    }
  }

  renderRules(rules) {
    if (!this.container) return;
    this.container.innerHTML = '';

    if (!rules || rules.length === 0) {
      this.container.innerHTML = '<p class="empty-state">No abstraction rules</p>';
      return;
    }

    rules.forEach(rule => {
      const card = this.createAbstractionCard(rule);
      this.container.appendChild(card);
    });
  }

  createAbstractionCard(rule) {
    const card = document.createElement('div');
    card.className = 'abstraction-card';

    const axis = document.createElement('div');
    axis.className = 'abstraction-axis';
    axis.textContent = window.t(`workspace.boards.abstraction.axes.${rule.axis}`);
    card.appendChild(axis);

    const observation = document.createElement('div');
    observation.className = 'abstraction-observation';
    observation.textContent = rule.observation;
    card.appendChild(observation);

    const appliedRule = document.createElement('div');
    appliedRule.className = 'abstraction-rule';
    appliedRule.textContent = rule.applied_rule;
    card.appendChild(appliedRule);

    const riskBadge = document.createElement('span');
    riskBadge.className = `risk-badge ${rule.risk_level}`;
    riskBadge.textContent = rule.risk_level.toUpperCase();
    card.appendChild(riskBadge);

    return card;
  }
}

export { AbstractionBoard };
