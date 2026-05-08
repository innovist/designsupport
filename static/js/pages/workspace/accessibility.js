// @MX:ANCHOR: [AUTO] Accessibility manager for WCAG 2.1 AA compliance
// @MX:REASON: Centralized ARIA management, keyboard navigation, and screen reader support

class WorkspaceAccessibility {
  constructor(workspace) {
    this.workspace = workspace;
    this.liveRegion = null;
    this.focusTrap = null;
    this.keyboardHandlers = new Map();
  }

  async initialize() {
    this.setupLiveRegions();
    this.setupKeyboardNavigation();
    this.setupFocusManagement();
    this.setupScreenReaderAnnouncements();
  }

  setupLiveRegions() {
    // Create polite live region for non-critical updates
    const politeRegion = document.createElement('div');
    politeRegion.id = 'a11y-live-polite';
    politeRegion.setAttribute('aria-live', 'polite');
    politeRegion.setAttribute('aria-atomic', 'true');
    politeRegion.className = 'visually-hidden';
    document.body.appendChild(politeRegion);

    // Create assertive live region for critical updates
    const assertiveRegion = document.createElement('div');
    assertiveRegion.id = 'a11y-live-assertive';
    assertiveRegion.setAttribute('aria-live', 'assertive');
    assertiveRegion.setAttribute('aria-atomic', 'true');
    assertiveRegion.className = 'visually-hidden';
    document.body.appendChild(assertiveRegion);

    this.liveRegion = {
      polite: politeRegion,
      assertive: assertiveRegion
    };
  }

  announce(message, priority = 'polite') {
    const region = this.liveRegion[priority];
    if (region) {
      region.textContent = '';
      setTimeout(() => {
        region.textContent = message;
      }, 100);
    }
  }

  announceStepChange(oldStep, newStep) {
    const message = window.t('workspace.a11y.stepChanged', {
      oldStep: window.t(`workspace.stepBar.steps.${oldStep}`),
      newStep: window.t(`workspace.stepBar.steps.${newStep}`)
    });
    this.announce(message, 'polite');
  }

  announceBoardChange(oldBoard, newBoard) {
    const message = window.t('workspace.a11y.boardChanged', {
      oldBoard: window.t(`workspace.boards.${oldBoard}.title`),
      newBoard: window.t(`workspace.boards.${newBoard}.title`)
    });
    this.announce(message, 'polite');
  }

  announceProgress(step, progress, message) {
    const announcement = window.t('workspace.a11y.progressUpdate', {
      step: window.t(`workspace.stepBar.steps.${step}`),
      progress: progress,
      message: message
    });
    this.announce(announcement, 'polite');
  }

  announceError(error) {
    const message = window.t('workspace.a11y.error', {
      error: error
    });
    this.announce(message, 'assertive');
  }

  setupKeyboardNavigation() {
    // Board tab navigation
    document.querySelectorAll('.board-tab').forEach(tab => {
      tab.setAttribute('tabindex', '0');
      tab.setAttribute('role', 'tab');

      tab.addEventListener('keydown', (e) => {
        this.handleTabKeydown(e, tab);
      });
    });

    // Card navigation
    document.addEventListener('keydown', (e) => {
      this.handleCardKeydown(e);
    });

    // Step navigation
    document.querySelectorAll('.step-item').forEach(step => {
      step.addEventListener('keydown', (e) => {
        this.handleStepKeydown(e, step);
      });
    });

    // Modal escape handling
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.handleEscape(e);
      }
    });
  }

  handleTabKeydown(event, tab) {
    const tabs = Array.from(document.querySelectorAll('.board-tab'));
    const currentIndex = tabs.indexOf(tab);

    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault();
        const nextTab = tabs[(currentIndex + 1) % tabs.length];
        nextTab.focus();
        nextTab.click();
        break;

      case 'ArrowLeft':
        event.preventDefault();
        const prevTab = tabs[(currentIndex - 1 + tabs.length) % tabs.length];
        prevTab.focus();
        prevTab.click();
        break;

      case 'Home':
        event.preventDefault();
        tabs[0].focus();
        tabs[0].click();
        break;

      case 'End':
        event.preventDefault();
        tabs[tabs.length - 1].focus();
        tabs[tabs.length - 1].click();
        break;
    }
  }

  handleCardKeydown(event) {
    const card = event.target.closest('.card, .evidence-card, .user-sketch-card, .reference-card, .generated-design-card, .abstraction-rule-card');

    if (!card) return;

    const cards = Array.from(card.parentElement.querySelectorAll(':scope > .card, :scope > .evidence-card, :scope > .user-sketch-card, :scope > .reference-card, :scope > .generated-design-card, :scope > .abstraction-rule-card'));
    const currentIndex = cards.indexOf(card);

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        const nextCard = cards[(currentIndex + 1) % cards.length];
        nextCard.focus();
        break;

      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        const prevCard = cards[(currentIndex - 1 + cards.length) % cards.length];
        prevCard.focus();
        break;

      case 'Enter':
      case ' ':
        event.preventDefault();
        card.click();
        break;
    }
  }

  handleStepKeydown(event, step) {
    const steps = Array.from(document.querySelectorAll('.step-item'));
    const currentIndex = steps.indexOf(step);

    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault();
        const nextStep = steps[(currentIndex + 1) % steps.length];
        nextStep.focus();
        nextStep.click();
        break;

      case 'ArrowLeft':
        event.preventDefault();
        const prevStep = steps[(currentIndex - 1 + steps.length) % steps.length];
        prevStep.focus();
        prevStep.click();
        break;

      case 'Home':
        event.preventDefault();
        steps[0].focus();
        steps[0].click();
        break;

      case 'End':
        event.preventDefault();
        steps[steps.length - 1].focus();
        steps[steps.length - 1].click();
        break;
    }
  }

  handleEscape(_event) {
    // Close any open modals
    const modals = document.querySelectorAll('.modal.open');
    modals.forEach(modal => {
      modal.classList.remove('open');
      this.restoreFocus();
    });

    // Close expanded panels
    const expandedPanels = document.querySelectorAll('[aria-expanded="true"]');
    expandedPanels.forEach(panel => {
      panel.setAttribute('aria-expanded', 'false');
    });
  }

  setupFocusManagement() {
    // Track last focused element before modal opens
    this.lastFocusedElement = null;

    // Manage focus for board switching
    this.workspace.state.subscribe('currentBoard', (boardId) => {
      this.focusBoard(boardId);
    });
  }

  focusBoard(boardId) {
    const board = document.getElementById(`board-${boardId}`);
    if (board) {
      // Find first focusable element in board
      const focusable = board.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable) {
        focusable.focus();
      }
    }
  }

  saveFocus() {
    this.lastFocusedElement = document.activeElement;
  }

  restoreFocus() {
    if (this.lastFocusedElement) {
      this.lastFocusedElement.focus();
      this.lastFocusedElement = null;
    }
  }

  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        } else if (!e.shiftKey && document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    });

    this.focusTrap = element;
    firstFocusable.focus();
  }

  releaseFocusTrap() {
    this.focusTrap = null;
    this.restoreFocus();
  }

  setupScreenReaderAnnouncements() {
    // Announce loading state changes
    this.workspace.state.subscribe('boards.chat.loading', (loading) => {
      if (loading) {
        this.announce(window.t('workspace.a11y.loading'), 'polite');
      }
    });

    // Announce errors
    this.workspace.state.subscribe('error', (error) => {
      if (error) {
        this.announceError(error);
      }
    });

    // Announce decision requirements
    this.workspace.state.subscribe('decisionRequired', (required) => {
      if (required) {
        this.announce(window.t('workspace.a11y.decisionRequired'), 'assertive');
      }
    });
  }

  updateAriaValues(element, values) {
    Object.entries(values).forEach(([key, value]) => {
      element.setAttribute(`aria-${key}`, value);
    });
  }

  setAriaLabel(element, label) {
    element.setAttribute('aria-label', label);
  }

  setAriaDescribedBy(element, descriptionId) {
    element.setAttribute('aria-describedby', descriptionId);
  }

  setAriaLive(element, level) {
    element.setAttribute('aria-live', level);
  }

  // High contrast mode support
  checkHighContrastMode() {
    return window.matchMedia('(prefers-contrast: high)').matches;
  }

  // Reduced motion support
  checkReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  applyReducedMotion() {
    if (this.checkReducedMotion()) {
      document.documentElement.style.setProperty('--transition-duration', '0.01ms');
    }
  }

  // Screen reader only content
  createScreenReaderOnlyText(text) {
    const span = document.createElement('span');
    span.className = 'visually-hidden';
    span.textContent = text;
    return span;
  }

  // Validate ARIA attributes
  validateARIA(element) {
    const errors = [];

    // Check for aria-label or aria-labelledby on interactive elements
    if (element.matches('button, a, input, select, textarea')) {
      const hasLabel = element.hasAttribute('aria-label') ||
                       element.hasAttribute('aria-labelledby') ||
                       element.textContent.trim();
      if (!hasLabel) {
        errors.push('Interactive element missing accessible label');
      }
    }

    // Check for aria-hidden conflicts
    if (element.hasAttribute('aria-hidden') && element.matches('button, a, input, select, textarea')) {
      errors.push('Interactive element has aria-hidden');
    }

    // Check for invalid aria-live values
    if (element.hasAttribute('aria-live')) {
      const liveValue = element.getAttribute('aria-live');
      if (!['polite', 'assertive', 'off'].includes(liveValue)) {
        errors.push(`Invalid aria-live value: ${liveValue}`);
      }
    }

    return errors;
  }
}

export { WorkspaceAccessibility };
