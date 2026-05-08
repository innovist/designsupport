// @MX:ANCHOR: [AUTO] Chat board module for AI conversation with evidence_refs and hypothesis badges
// @MX:REASON: Manages chat interface, message rendering, and evidence linking

class ChatBoard {
  constructor(workspace) {
    this.workspace = workspace;
    this.container = null;
  }

  async initialize() {
    this.container = document.getElementById('chat-messages');
    this.setupEventListeners();
  }

  async load() {
    try {
      this.workspace.skeleton.showSkeleton('chat-messages', 'chat');
      
      const messages = await this.workspace.api.getMessages(this.workspace.state.sessionId);
      this.workspace.state.set('boards.chat.messages', messages);
      
      this.renderMessages(messages);
    } catch (error) {
      console.error('Failed to load chat messages:', error);
      this.workspace.emptyState.showEmptyState('chat', 'networkError', this.container);
    } finally {
      this.workspace.skeleton.hideSkeleton('chat-messages');
    }
  }

  setupEventListeners() {
    const sendBtn = document.getElementById('chat-send');
    const input = document.getElementById('chat-input');

    sendBtn?.addEventListener('click', () => this.sendMessage());
    input?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  async sendMessage() {
    const input = document.getElementById('chat-input');
    const content = input?.value.trim();
    
    if (!content) return;

    try {
      // Add user message to UI
      this.addMessageToUI({ role: 'user', content });
      input.value = '';

      // Send to API
      const response = await this.workspace.api.sendMessage(
        this.workspace.state.sessionId,
        content
      );

      // Add AI message to UI
      this.addMessageToUI(response);

      // Update state
      const messages = this.workspace.state.get('boards.chat.messages') || [];
      messages.push({ role: 'user', content });
      messages.push(response);
      this.workspace.state.set('boards.chat.messages', messages);
    } catch (error) {
      console.error('Failed to send message:', error);
      this.workspace.emptyState.showEmptyState('chat', 'networkError', this.container);
    }
  }

  renderMessages(messages) {
    if (!this.container) return;

    this.container.innerHTML = '';

    if (!messages || messages.length === 0) {
      this.container.innerHTML = '<div class="empty-state"><p>No messages yet</p></div>';
      return;
    }

    messages.forEach(message => {
      this.addMessageToUI(message);
    });

    // Auto-scroll to latest
    this.container.scrollTop = this.container.scrollHeight;
  }

  addMessageToUI(message) {
    if (!this.container) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${message.role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // SPEC-05: Markdown whitelist renderer (no raw HTML)
    const content = this.renderMarkdown(message.content);
    bubble.innerHTML = content;

    messageDiv.appendChild(bubble);

    // Add evidence references for AI messages
    if (message.evidence_refs && message.evidence_refs.length > 0) {
      const evidenceContainer = document.createElement('div');
      evidenceContainer.className = 'evidence-refs';

      message.evidence_refs.forEach(ref => {
        const refBadge = document.createElement('span');
        refBadge.className = 'evidence-ref';
        refBadge.textContent = `📎 ${ref.id}`;
        refBadge.addEventListener('click', () => this.navigateToEvidence(ref.id));
        evidenceContainer.appendChild(refBadge);
      });

      messageDiv.appendChild(evidenceContainer);
    }

    // Add hypothesis badge
    if (message.is_hypothesis) {
      const hypothesisBadge = document.createElement('span');
      hypothesisBadge.className = 'hypothesis-badge';
      hypothesisBadge.textContent = window.t('workspace.boards.chat.hypothesis');
      messageDiv.appendChild(hypothesisBadge);
    }

    this.container.appendChild(messageDiv);
    this.container.scrollTop = this.container.scrollHeight;
  }

  // SPEC-05: Markdown whitelist renderer - only safe formatting, no raw HTML
  renderMarkdown(text) {
    if (!text) return '';

    // Escape HTML first to prevent XSS
    let safeText = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Apply safe markdown formatting (whitelist approach)
    // Bold: **text** or __text__
    safeText = safeText.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    safeText = safeText.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    safeText = safeText.replace(/\*(.+?)\*/g, '<em>$1</em>');
    safeText = safeText.replace(/_(.+?)_/g, '<em>$1</em>');

    // Code: `text`
    safeText = safeText.replace(/`(.+?)`/g, '<code>$1</code>');

    // Line breaks
    safeText = safeText.replace(/\n/g, '<br>');

    // Links: [text](url) - but only allow https/http links
    safeText = safeText.replace(/\[(.+?)\]\((https?:\/\/.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    return safeText;
  }

  navigateToEvidence(evidenceId) {
    // Switch to evidence board
    this.workspace.boardManager.switchBoard('evidence');

    // Wait for board to load, then highlight the evidence
    setTimeout(() => {
      const evidenceCard = document.querySelector(`[data-evidence-id="${evidenceId}"]`);
      if (evidenceCard) {
        evidenceCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        evidenceCard.classList.add('highlighted');

        // Remove highlight after animation
        setTimeout(() => {
          evidenceCard.classList.remove('highlighted');
        }, 2000);
      }
    }, 100);
  }
}

export { ChatBoard };
