// @MX:ANCHOR: [AUTO] Single source of truth for workspace state with reactive updates
// @MX:REASON: Centralized state management accessed by all boards and components

class StateStore {
  constructor() {
    this.state = {
      sessionId: null,
      currentStep: null,
      mode: 'standard',
      autoMode: {
        state: 'idle',
        taskLog: null,
        progress: 0
      },
      boards: {
        chat: { messages: [], loading: false },
        evidence: { insights: [], filters: {}, sort: 'credibility' },
        sketch: { original: null, interpretation: null, actions: [] },
        reference: { clusters: [], grid: [], selected: null },
        abstraction: { rules: [] },
        generation: { results: [], comparison: null },
        decision: { candidates: [], selected: null, log: [] },
        spec: { sections: [], rejected_concepts: [] }
      },
      decisionPanel: {
        briefScore: 0,
        conceptScores: { creativity: 0, feasibility: 0, marketFit: 0 },
        selectedSketch: null,
        selectedReferences: [],
        nextAction: null,
        nextActionReason: null
      }
    };
    this.listeners = new Map();

    // @MX:NOTE: 17-step to board mapping from SPEC-05 §5.1
    this.stepBoardMapping = {
      1: 'chat',
      2: 'chat',
      3: 'sketch',
      4: 'chat',
      5: 'evidence',
      6: 'chat',
      7: 'decision',
      8: 'decision',
      9: 'reference',
      10: 'reference',
      11: 'reference',
      12: 'abstraction',
      13: 'generation',
      14: 'generation',
      15: 'generation',
      16: 'spec',
      17: 'decision'
    };

    // @MX:NOTE: Auto mode states from SPEC-05 §5.2
    this.autoModeStates = [
      'queued',
      'researching',
      'concepting',
      'referencing',
      'abstracting',
      'generating',
      'documenting',
      'review_ready',
      'failed'
    ];
  }

  get(path) {
    return path.split('.').reduce((current, key) => current?.[key], this.state);
  }

  set(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((current, key) => current[key], this.state);
    target[lastKey] = value;
    this.notify(path, value);
  }

  setSession(session) {
    this.state.sessionId = session.id;
    this.state.currentStep = session.current_step;
    this.state.mode = session.mode;
    this.notify('session', session);
  }

  setCurrentStep(step) {
    this.state.currentStep = step;
    this.notify('currentStep', step);

    // Auto-activate correct board based on step
    const board = this.stepBoardMapping[step];
    if (board) {
      this.notify('activateBoard', board);
    }
  }

  subscribe(path, callback) {
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set());
    }
    this.listeners.get(path).add(callback);
  }

  unsubscribe(path, callback) {
    if (this.listeners.has(path)) {
      this.listeners.get(path).delete(callback);
    }
  }

  notify(path, value) {
    const callbacks = this.listeners.get(path);
    if (callbacks) {
      callbacks.forEach(callback => callback(value));
    }
  }

  // Auto mode state management
  setAutoModeState(state, taskLog = null, progress = 0) {
    if (!this.autoModeStates.includes(state)) {
      console.warn('Invalid auto mode state:', state);
      return;
    }

    this.state.autoMode.state = state;
    this.state.autoMode.taskLog = taskLog;
    this.state.autoMode.progress = progress;

    this.notify('autoModeState', state);
    this.notify('autoModeTaskLog', taskLog);
    this.notify('autoModeProgress', progress);

    // Announce state change for screen readers
    this.announceAutoModeState(state);
  }

  announceAutoModeState(state) {
    const message = window.t(`workspace.autoMode.states.${state}`);
    const announcement = `Auto mode: ${message}`;

    // Use aria-live region for screen reader announcement
    const liveRegion = document.getElementById('workspace-live-region');
    if (liveRegion) {
      liveRegion.textContent = announcement;
    }
  }

  getBoardForStep(step) {
    return this.stepBoardMapping[step];
  }

  getAllSteps() {
    return Object.keys(this.stepBoardMapping).map(Number);
  }

  getAutoModeState() {
    return this.state.autoMode.state;
  }
}

export { StateStore };
