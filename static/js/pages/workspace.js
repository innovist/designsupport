// @MX:ANCHOR: [AUTO] Main workspace entry point that initializes all boards and core systems
// @MX:REASON: Single entry point for workspace initialization, called by workspace.html

import { BoardManager } from './boards/manager.js';
import { StateStore } from './state.js';
import { WorkspaceAPI } from './api.js';
import { SkeletonManager } from './skeleton.js';
import { EmptyStateManager } from './empty-states.js';
import { WorkspaceAccessibility } from './accessibility.js';

class Workspace {
  constructor() {
    this.state = new StateStore();
    this.api = new WorkspaceAPI();
    this.skeleton = new SkeletonManager();
    this.emptyState = new EmptyStateManager();
    this.accessibility = new WorkspaceAccessibility(this);
    this.boardManager = null;
    this.sessionId = null;
  }

  async init(sessionId) {
    try {
      this.sessionId = sessionId || null;

      // Initialize accessibility
      await this.accessibility.initialize();

      // Initialize board manager
      this.boardManager = new BoardManager(this);

      if (this.sessionId) {
        await this.loadSessionData();
      } else {
        this.state.setCurrentStep(1);
      }

      // Set up event listeners
      this.setupEventListeners();

      // Initialize boards
      this.boardManager.initialize();

      // Show initial board
      this.boardManager.switchBoard('chat');
    } catch (error) {
      console.error('Workspace initialization failed:', error);
      this.showError('workspace.initFailed');
    }
  }

  async loadSessionData() {
    try {
      const session = await this.api.getSession(this.sessionId);
      this.state.setSession(session);
    } catch (error) {
      console.error('Failed to load session data:', error);
      throw error;
    }
  }

  setupEventListeners() {
    // Board tab switching
    document.querySelectorAll('.board-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const boardId = e.target.closest('.board-tab').dataset.board;
        this.boardManager.switchBoard(boardId);
      });
    });

    // Step navigation
    document.querySelectorAll('.step-item').forEach(step => {
      step.addEventListener('click', (e) => {
        const stepKey = e.target.closest('.step-item').dataset.step;
        this.navigateToStep(stepKey);
      });
    });

    // Decision panel toggle
    const toggleBtn = document.getElementById('toggle-decision-panel');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        document.querySelector('.decision-panel').classList.toggle('collapsed');
      });
    }

    // Listen for language changes
    window.addEventListener('languageChanged', () => {
      this.boardManager.refreshCurrentBoard();
    });
  }

  async navigateToStep(stepKey) {
    try {
      const oldStep = this.state.currentStep;
      if (this.sessionId) {
        await this.api.getSession(this.sessionId);
      }

      // Update current step and refresh boards
      this.state.setCurrentStep(stepKey);
      this.boardManager.refreshAllBoards();

      // Announce step change for accessibility
      if (oldStep && oldStep !== stepKey) {
        this.accessibility.announceStepChange(oldStep, stepKey);
      }
    } catch (error) {
      console.error('Navigation failed:', error);
      this.accessibility.announceError(error.message);
      this.showError('workspace.navigationFailed');
    }
  }

  showError(errorKey) {
    console.error('Workspace error:', errorKey);
  }
}

// Initialize workspace when DOM is ready
let workspace = null;

document.addEventListener('DOMContentLoaded', async () => {
  const root = document.querySelector('.workspace-container');
  const params = new URLSearchParams(window.location.search);
  const sessionId = root?.dataset.sessionId || params.get('session') || params.get('session_id');
  workspace = new Workspace();
  await workspace.init(sessionId);
});

window.workspace = workspace;
