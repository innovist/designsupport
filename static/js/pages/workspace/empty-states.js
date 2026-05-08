// @MX:ANCHOR: [AUTO] Empty state manager for all error and no-data scenarios
// @MX:REASON: Consistent empty state presentation with actionable recovery options

class EmptyStateManager {
  constructor() {
    this.states = {
      noTrendData: {
        icon: '📊',
        titleKey: 'workspace.emptyStates.noTrendData.title',
        descriptionKey: 'workspace.emptyStates.noTrendData.description',
        actions: []
      },
      noReferences: {
        icon: '🔍',
        titleKey: 'workspace.emptyStates.noReferences.title',
        descriptionKey: 'workspace.emptyStates.noReferences.description',
        actions: []
      },
      licenseRisk: {
        icon: '⚠️',
        titleKey: 'workspace.emptyStates.licenseRisk.title',
        descriptionKey: 'workspace.emptyStates.licenseRisk.description',
        actions: []
      },
      modelFailure: {
        icon: '🤖',
        titleKey: 'workspace.emptyStates.modelFailure.title',
        descriptionKey: 'workspace.emptyStates.modelFailure.description',
        actions: [
          { labelKey: 'common.retry', action: 'retry' }
        ]
      },
      autoUncertainty: {
        icon: '❓',
        titleKey: 'workspace.emptyStates.autoUncertainty.title',
        descriptionKey: 'workspace.emptyStates.autoUncertainty.description',
        actions: []
      },
      parseFailure: {
        icon: '📄',
        titleKey: 'workspace.emptyStates.parseFailure.title',
        descriptionKey: 'workspace.emptyStates.parseFailure.description',
        actions: [
          { labelKey: 'common.retry', action: 'retry' }
        ]
      },
      networkError: {
        icon: '🌐',
        titleKey: 'workspace.emptyStates.networkError.title',
        descriptionKey: 'workspace.emptyStates.networkError.description',
        actions: [
          { labelKey: 'common.retry', action: 'retry' }
        ]
      },
      quotaExceeded: {
        icon: '📊',
        titleKey: 'workspace.emptyStates.quotaExceeded.title',
        descriptionKey: 'workspace.emptyStates.quotaExceeded.description',
        actions: []
      },
      insufficientEvidence: {
        icon: '🔬',
        titleKey: 'workspace.emptyStates.insufficientEvidence.title',
        descriptionKey: 'workspace.emptyStates.insufficientEvidence.description',
        actions: []
      },
      permissionDenied: {
        icon: '🔒',
        titleKey: 'workspace.emptyStates.permissionDenied.title',
        descriptionKey: 'workspace.emptyStates.permissionDenied.description',
        actions: []
      }
    };
  }

  showEmptyState(boardId, reason, container = null) {
    const targetContainer = container || document.querySelector(`#board-${boardId} .board-content`);
    if (!targetContainer) return;

    const stateConfig = this.states[reason] || this.states.noTrendData;
    const emptyState = this.createEmptyState(stateConfig);
    
    targetContainer.innerHTML = '';
    targetContainer.appendChild(emptyState);
  }

  createEmptyState(config) {
    const container = document.createElement('div');
    container.className = 'empty-state';

    const icon = document.createElement('div');
    icon.className = 'empty-state-icon';
    icon.textContent = config.icon;
    container.appendChild(icon);

    const title = document.createElement('h3');
    title.className = 'empty-state-title';
    title.textContent = window.t(config.titleKey);
    container.appendChild(title);

    const description = document.createElement('p');
    description.className = 'empty-state-description';
    description.textContent = window.t(config.descriptionKey);
    container.appendChild(description);

    if (config.actions.length > 0) {
      const actions = document.createElement('div');
      actions.className = 'empty-state-actions';

      config.actions.forEach(actionConfig => {
        const button = document.createElement('button');
        button.className = 'btn btn-primary';
        button.textContent = window.t(actionConfig.labelKey);
        button.addEventListener('click', () => this.handleAction(actionConfig.action));
        actions.appendChild(button);
      });

      container.appendChild(actions);
    }

    return container;
  }

  handleAction(action) {
    switch (action) {
      case 'retry':
        window.location.reload();
        break;
      default:
        console.warn('Unknown action:', action);
    }
  }
}

export { EmptyStateManager };
