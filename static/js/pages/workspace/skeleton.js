// @MX:ANCHOR: [AUTO] Skeleton loading manager for all async operations with task log display
// @MX:REASON: Consistent skeleton loading experience across all boards with progress feedback

class SkeletonManager {
  constructor() {
    this.activeSkeletons = new Map();
  }

  showSkeleton(boardId, type, options = {}) {
    const container = document.querySelector(`[data-skeleton="${boardId}"]`);
    if (!container) return;

    // Remove existing skeleton
    this.hideSkeleton(boardId);

    // Create skeleton element
    const skeleton = this.createSkeleton(type, options);
    container.innerHTML = '';
    container.appendChild(skeleton);

    // Track active skeleton
    this.activeSkeletons.set(boardId, { element: skeleton, type, options });

    // Show task log if provided
    if (options.taskLog) {
      this.showTaskLog(container, options.taskLog);
    }
  }

  hideSkeleton(boardId) {
    const container = document.querySelector(`[data-skeleton="${boardId}"]`);
    if (!container) return;

    const skeletonData = this.activeSkeletons.get(boardId);
    if (skeletonData) {
      container.innerHTML = '';
      this.activeSkeletons.delete(boardId);
    }
  }

  createSkeleton(type, options) {
    const skeleton = document.createElement('div');
    skeleton.className = `skeleton-${type}`;

    switch (type) {
      case 'cards':
        return this.createCardsSkeleton(options.count || 4);
      case 'chat':
        return this.createChatSkeleton(options.count || 5);
      case 'image-grid':
        return this.createImageGridSkeleton(options.count || 8);
      case 'split-3':
        return this.createSplit3Skeleton();
      case 'text':
        return this.createTextSkeleton(options.lines || 4);
      case 'list':
        return this.createListSkeleton(options.count || 5);
      case 'abstraction-rules':
        return this.createAbstractionRulesSkeleton(options.count || 6);
      case 'generation-results':
        return this.createGenerationResultsSkeleton(options.count || 4);
      default:
        return skeleton;
    }
  }

  createCardsSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-cards';

    for (let i = 0; i < count; i++) {
      const card = document.createElement('div');
      card.className = 'skeleton-card';
      container.appendChild(card);
    }

    return container;
  }

  createChatSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-chat';

    for (let i = 0; i < count; i++) {
      const message = document.createElement('div');
      message.className = `skeleton-message ${i % 2 === 0 ? 'ai' : 'user'}`;
      container.appendChild(message);
    }

    return container;
  }

  createImageGridSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-grid';

    for (let i = 0; i < count; i++) {
      const item = document.createElement('div');
      item.className = 'skeleton-grid-item';
      container.appendChild(item);
    }

    return container;
  }

  createSplit3Skeleton() {
    const container = document.createElement('div');
    container.style.display = 'grid';
    container.style.gridTemplateColumns = '1fr 1fr 1fr';
    container.style.gap = '16px';
    container.style.height = '400px';

    for (let i = 0; i < 3; i++) {
      const panel = document.createElement('div');
      panel.className = 'skeleton-text';
      container.appendChild(panel);
    }

    return container;
  }

  createTextSkeleton(lines) {
    const container = document.createElement('div');
    container.className = 'skeleton-text';

    for (let i = 0; i < lines; i++) {
      const line = document.createElement('div');
      line.className = 'skeleton-text-line';
      if (i === lines - 1) {
        line.style.width = '60%';
      }
      container.appendChild(line);
    }

    return container;
  }

  createListSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-list';

    for (let i = 0; i < count; i++) {
      const item = document.createElement('div');
      item.className = 'skeleton-list-item';
      container.appendChild(item);
    }

    return container;
  }

  createAbstractionRulesSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-cards';

    for (let i = 0; i < count; i++) {
      const card = document.createElement('div');
      card.className = 'skeleton-card skeleton-abstraction-card';
      container.appendChild(card);
    }

    return container;
  }

  createGenerationResultsSkeleton(count) {
    const container = document.createElement('div');
    container.className = 'skeleton-grid';

    for (let i = 0; i < count; i++) {
      const item = document.createElement('div');
      item.className = 'skeleton-grid-item skeleton-generation-item';
      container.appendChild(item);
    }

    return container;
  }

  showTaskLog(container, taskLog) {
    const logElement = document.createElement('div');
    logElement.className = 'task-log';
    logElement.innerHTML = `
      <div class="task-log-step">${taskLog.step}</div>
      <div class="task-log-feature">${taskLog.featureKey}</div>
      <div class="task-log-progress">Attempt ${taskLog.attempt} - ${taskLog.progress}%</div>
    `;
    container.appendChild(logElement);
  }
}

export { SkeletonManager };
