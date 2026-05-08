class SketchBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.originalPanel = null;
    this.interpretationPanel = null;
  }

  async initialize() {
    this.originalPanel = document.getElementById('sketch-upload-area');
    this.interpretationPanel = document.getElementById('sketch-interpretation-content');
    this.setupEventListeners();
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('sketch-upload', 'image');
      this.workspace.skeleton.showSkeleton('sketch-interpretation', 'text');
      
      const sketchData = await this.workspace.api.getSketch(this.workspace.state.sessionId);
      this.workspace.state.set('boards.sketch.original', sketchData.original);
      this.workspace.state.set('boards.sketch.interpretation', sketchData.interpretation);
      
      this.renderOriginal(sketchData.original);
      this.renderInterpretation(sketchData.interpretation);
    } catch (error) {
      console.error('Failed to load sketch:', error);
      this.workspace.emptyState.showEmptyState('sketch', 'modelFailure', this.originalPanel);
    } finally {
      this.workspace.skeleton.hideSkeleton('sketch-upload');
      this.workspace.skeleton.hideSkeleton('sketch-interpretation');
    }
  }

  setupEventListeners() {
    const uploadArea = document.getElementById('sketch-upload-area');
    const fileInput = document.getElementById('sketch-file-input');

    uploadArea?.addEventListener('click', () => fileInput?.click());
    fileInput?.addEventListener('change', (e) => this.handleFileUpload(e));

    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.addEventListener('click', () => this.handleAction(btn.dataset.action));
    });
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // SPEC-05: Prevent overwrite - check if sketch exists and show modal
    const existingSketch = this.workspace.state.get('boards.sketch.original');
    if (existingSketch) {
      const shouldSaveAsNew = await this.showOverwritePreventionModal();
      if (!shouldSaveAsNew) {
        return; // User cancelled
      }
    }

    try {
      const result = await this.workspace.api.uploadSketch(
        this.workspace.state.sessionId,
        file
      );

      this.workspace.state.set('boards.sketch.original', result);
      this.renderOriginal(result);

      // Load interpretation
      await this.loadInterpretation();
    } catch (error) {
      console.error('Upload failed:', error);
      this.workspace.emptyState.showEmptyState('sketch', 'networkError', this.originalPanel);
    }
  }

  // SPEC-05: Show modal for "save as new version" to prevent overwrite
  async showOverwritePreventionModal() {
    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-content" role="dialog" aria-labelledby="sketch-overwrite-title">
          <h2 id="sketch-overwrite-title">${window.t('workspace.boards.sketch.saveAsNew')}</h2>
          <p>${window.t('workspace.boards.sketch.overwriteWarning')}</p>
          <div class="modal-actions">
            <button class="btn btn-secondary" data-action="cancel">${window.t('common.cancel')}</button>
            <button class="btn btn-primary" data-action="save">${window.t('common.save')}</button>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      const cancelBtn = modal.querySelector('[data-action="cancel"]');
      const saveBtn = modal.querySelector('[data-action="save"]');

      cancelBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
        resolve(false);
      });

      saveBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
        resolve(true);
      });

      // Focus trap for accessibility
      saveBtn.focus();
    });
  }

  async loadInterpretation() {
    try {
      this.workspace.skeleton.showSkeleton('sketch-interpretation', 'text');
      
      const interpretation = await this.workspace.api.getSketchInterpretation(
        this.workspace.state.sessionId
      );

      this.workspace.state.set('boards.sketch.interpretation', interpretation);
      this.renderInterpretation(interpretation);
    } finally {
      this.workspace.skeleton.hideSkeleton('sketch-interpretation');
    }
  }

  renderOriginal(sketch) {
    if (!this.originalPanel) return;

    if (!sketch) {
      this.originalPanel.innerHTML = '<p class="empty-state">No sketch uploaded</p>';
      return;
    }

    this.originalPanel.innerHTML = '';
    const img = document.createElement('img');
    img.src = sketch.url;
    img.alt = 'Uploaded sketch';
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.objectFit = 'contain';
    this.originalPanel.appendChild(img);
  }

  renderInterpretation(interpretation) {
    if (!this.interpretationPanel) return;

    if (!interpretation) {
      this.interpretationPanel.innerHTML = '<p class="empty-state">No interpretation available</p>';
      return;
    }

    this.interpretationPanel.innerHTML = '';

    // Hypothesis badge
    if (interpretation.is_hypothesis) {
      const badge = document.createElement('span');
      badge.className = 'hypothesis-badge';
      badge.textContent = window.t('workspace.boards.chat.hypothesis');
      this.interpretationPanel.appendChild(badge);
    }

    // Intent
    if (interpretation.intent) {
      const intent = document.createElement('div');
      intent.innerHTML = `<strong>Intent:</strong> ${interpretation.intent}`;
      this.interpretationPanel.appendChild(intent);
    }

    // Form
    if (interpretation.form) {
      const form = document.createElement('div');
      form.innerHTML = `<strong>Form:</strong> ${interpretation.form}`;
      this.interpretationPanel.appendChild(form);
    }

    // Structure
    if (interpretation.structure) {
      const structure = document.createElement('div');
      structure.innerHTML = `<strong>Structure:</strong> ${interpretation.structure}`;
      this.interpretationPanel.appendChild(structure);
    }

    // Uncertain elements
    if (interpretation.uncertain_elements && interpretation.uncertain_elements.length > 0) {
      const uncertain = document.createElement('div');
      uncertain.innerHTML = '<strong>Uncertain Elements:</strong>';
      const list = document.createElement('ul');
      interpretation.uncertain_elements.forEach(elem => {
        const li = document.createElement('li');
        li.textContent = elem;
        list.appendChild(li);
      });
      uncertain.appendChild(list);
      this.interpretationPanel.appendChild(uncertain);
    }

    // Questions
    if (interpretation.questions && interpretation.questions.length > 0) {
      const questions = document.createElement('div');
      questions.innerHTML = '<strong>Questions:</strong>';
      const list = document.createElement('ul');
      interpretation.questions.forEach(q => {
        const li = document.createElement('li');
        li.textContent = q;
        list.appendChild(li);
      });
      questions.appendChild(list);
      this.interpretationPanel.appendChild(questions);
    }
  }

  async handleAction(action) {
    try {
      const result = await this.workspace.api.executeSketchAction(
        this.workspace.state.sessionId,
        action
      );
      if (result?.sketch) {
        this.workspace.state.addNotification('success', 'Action completed');
      }
    } catch (error) {
      console.error('Action failed:', error);
    }
  }
}

export { SketchBoard };
