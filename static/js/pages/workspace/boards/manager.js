// @MX:ANCHOR: [AUTO] Board manager that handles switching between 7 boards and coordinates updates
// @MX:REASON: Central board management accessed by main workspace and navigation

class BoardManager {
  constructor(workspace) {
    this.workspace = workspace;
    this.boards = {};
    this.currentBoard = null;
  }

  async initialize() {
    // Import and initialize all boards
    const { ChatBoard } = await import('./chat.js');
    const { EvidenceBoard } = await import('./evidence.js');
    const { SketchBoard } = await import('./sketch.js');
    const { ReferenceBoard } = await import('./reference.js');
    const { AbstractionBoard } = await import('./abstraction.js');
    const { GenerationBoard } = await import('./generation.js');
    const { DecisionBoard } = await import('./decision.js');

    this.boards = {
      chat: new ChatBoard(this.workspace),
      evidence: new EvidenceBoard(this.workspace),
      sketch: new SketchBoard(this.workspace),
      reference: new ReferenceBoard(this.workspace),
      abstraction: new AbstractionBoard(this.workspace),
      generation: new GenerationBoard(this.workspace),
      decision: new DecisionBoard(this.workspace)
    };

    // Initialize all boards
    await Promise.all(
      Object.values(this.boards).map(board => board.initialize())
    );
  }

  async switchBoard(boardId) {
    if (this.currentBoard === boardId) return;

    const oldBoard = this.currentBoard;

    // Hide current board
    if (this.currentBoard) {
      document.querySelector(`#board-${this.currentBoard}`)?.classList.remove('active');
      document.querySelector(`[data-board="${this.currentBoard}"]`)?.classList.remove('tab-active');
      document.querySelector(`[data-board="${this.currentBoard}"]`)?.setAttribute('aria-selected', 'false');
    }

    // Show new board
    this.currentBoard = boardId;
    const boardElement = document.querySelector(`#board-${boardId}`);
    const tabElement = document.querySelector(`[data-board="${boardId}"]`);

    boardElement?.classList.add('active');
    tabElement?.classList.add('tab-active');
    tabElement?.setAttribute('aria-selected', 'true');

    // Announce board change for accessibility
    if (oldBoard && oldBoard !== boardId) {
      this.workspace.accessibility.announceBoardChange(oldBoard, boardId);
    }

    if (this.workspace.sessionId) {
      await this.boards[boardId]?.load();
    }
  }

  async refreshCurrentBoard() {
    if (this.currentBoard && this.workspace.sessionId) {
      await this.boards[this.currentBoard]?.load();
    }
  }

  async refreshAllBoards() {
    if (!this.workspace.sessionId) return;
    await Promise.all(Object.values(this.boards).map(board => board.load()));
  }

  getBoard(boardId) {
    return this.boards[boardId];
  }
}

export { BoardManager };
