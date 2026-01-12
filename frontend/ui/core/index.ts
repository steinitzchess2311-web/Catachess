/**
 * Frontend Core Module
 *
 * Unified window management system with drag, resize, focus, and snap capabilities.
 * Provides a complete solution for managing multiple panels/windows in a desktop-like interface.
 */

// Export all submodules
export * from './pointer';
export * from './focus';
export * from './drag';
export * from './resize';
export * from './scroll';
export * from './utils';

import { Draggable, makeDraggable } from './drag';
import { Resizable, makeResizable } from './resize';
import { focusManager } from './focus';
import { snapManager, windowStateManager } from './utils';
import { ScrollController, createScrollController } from './scroll';

/**
 * Panel configuration options
 */
export interface PanelOptions {
  id: string;
  element: HTMLElement;
  draggable?: boolean;
  resizable?: boolean;
  focusable?: boolean;
  scrollable?: boolean;
  snapEnabled?: boolean;
  dragHandle?: HTMLElement | string;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
}

/**
 * Managed panel with all features
 */
export class Panel {
  public id: string;
  public element: HTMLElement;
  private draggable?: Draggable;
  private resizable?: Resizable;
  private scrollController?: ScrollController;
  private options: PanelOptions;
  private unsubscribers: (() => void)[] = [];

  constructor(options: PanelOptions) {
    this.id = options.id;
    this.element = options.element;
    this.options = options;

    // Set data attribute for focus management
    this.element.setAttribute('data-focus-id', this.id);

    this.initialize();
  }

  private initialize(): void {
    // Setup dragging
    if (this.options.draggable !== false) {
      this.draggable = makeDraggable(this.element, {
        handle: this.options.dragHandle,
        constrainToViewport: true,
        onDragStart: this.handleDragStart.bind(this),
        onDrag: this.handleDrag.bind(this),
        onDragEnd: this.handleDragEnd.bind(this),
      });
    }

    // Setup resizing
    if (this.options.resizable !== false) {
      this.resizable = makeResizable(this.element, {
        minWidth: this.options.minWidth || 200,
        minHeight: this.options.minHeight || 150,
        maxWidth: this.options.maxWidth,
        maxHeight: this.options.maxHeight,
        constrainToViewport: true,
      });
    }

    // Setup focus management
    if (this.options.focusable !== false) {
      const unsubFocus = focusManager.register(this.id, this.element);
      this.unsubscribers.push(unsubFocus);
    }

    // Setup scroll controller
    if (this.options.scrollable) {
      this.scrollController = createScrollController(this.element);
    }

    // Add panel class
    this.element.classList.add('panel');
  }

  private handleDragStart(): void {
    // If snapped or maximized, restore first
    const state = windowStateManager.getState(this.id);
    if (state && (state.isMaximized || state.isSnapped)) {
      windowStateManager.restore(this.id, this.element);
    }

    // Hide snap preview when dragging starts
    snapManager.hideSnapPreview();
  }

  private handleDrag(): void {
    if (!this.options.snapEnabled) return;

    // Get drag position
    const position = this.draggable?.getPosition();
    if (!position) return;

    // Detect snap zone
    const zone = snapManager.detectSnapZone(position.x, position.y);

    if (zone) {
      snapManager.showSnapPreview(zone);
    } else {
      snapManager.hideSnapPreview();
    }
  }

  private handleDragEnd(): void {
    if (!this.options.snapEnabled) return;

    const position = this.draggable?.getPosition();
    if (!position) return;

    const zone = snapManager.detectSnapZone(position.x, position.y);

    if (zone) {
      windowStateManager.snap(this.id, this.element, zone);
    }

    snapManager.hideSnapPreview();
  }

  /**
   * Focus this panel
   */
  public focus(): void {
    focusManager.focus(this.id);
  }

  /**
   * Maximize panel
   */
  public maximize(): void {
    windowStateManager.maximize(this.id, this.element);
  }

  /**
   * Restore panel
   */
  public restore(): void {
    windowStateManager.restore(this.id, this.element);
  }

  /**
   * Toggle maximize/restore
   */
  public toggleMaximize(): void {
    windowStateManager.toggleMaximize(this.id, this.element);
  }

  /**
   * Enable dragging
   */
  public enableDrag(): void {
    this.draggable?.enable();
  }

  /**
   * Disable dragging
   */
  public disableDrag(): void {
    this.draggable?.disable();
  }

  /**
   * Enable resizing
   */
  public enableResize(): void {
    this.resizable?.enable();
  }

  /**
   * Disable resizing
   */
  public disableResize(): void {
    this.resizable?.disable();
  }

  /**
   * Get scroll controller
   */
  public getScrollController(): ScrollController | undefined {
    return this.scrollController;
  }

  /**
   * Destroy panel and cleanup
   */
  public destroy(): void {
    this.draggable?.destroy();
    this.resizable?.destroy();
    this.scrollController?.destroy();
    this.unsubscribers.forEach((unsub) => unsub());
    this.element.classList.remove('panel');
    windowStateManager.clearState(this.id);
  }
}

/**
 * Create a managed panel
 */
export function createPanel(options: PanelOptions): Panel {
  return new Panel(options);
}
