/**
 * Resize Module - Element resizing functionality
 *
 * Provides resize handles for elements with constraint support,
 * aspect ratio locking, and minimum/maximum size constraints.
 */

import { pointerManager, PointerEventData } from '../pointer';

export interface ResizeOptions {
  handles?: ResizeHandle[]; // Which handles to enable
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
  aspectRatio?: number; // Lock aspect ratio (width / height)
  grid?: number; // Snap to grid
  constrainToParent?: boolean;
  constrainToViewport?: boolean;
  onResizeStart?: (element: HTMLElement, size: Size) => boolean | void;
  onResize?: (element: HTMLElement, size: Size) => void;
  onResizeEnd?: (element: HTMLElement, size: Size) => void;
  disabled?: boolean;
}

export type ResizeHandle =
  | 'n'  // North (top)
  | 's'  // South (bottom)
  | 'e'  // East (right)
  | 'w'  // West (left)
  | 'ne' // North-east (top-right)
  | 'nw' // North-west (top-left)
  | 'se' // South-east (bottom-right)
  | 'sw'; // South-west (bottom-left)

export interface Size {
  width: number;
  height: number;
  left?: number;
  top?: number;
}

export interface ResizeState {
  isResizing: boolean;
  handle: ResizeHandle | null;
  startX: number;
  startY: number;
  startWidth: number;
  startHeight: number;
  startLeft: number;
  startTop: number;
}

/**
 * Resizable element controller
 */
export class Resizable {
  private element: HTMLElement;
  private options: ResizeOptions;
  private state: ResizeState;
  private handleElements: Map<ResizeHandle, HTMLElement> = new Map();
  private unsubscribers: (() => void)[] = [];

  constructor(element: HTMLElement, options: ResizeOptions = {}) {
    this.element = element;
    this.options = {
      handles: ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'],
      minWidth: 100,
      minHeight: 100,
      ...options,
    };

    this.state = {
      isResizing: false,
      handle: null,
      startX: 0,
      startY: 0,
      startWidth: 0,
      startHeight: 0,
      startLeft: 0,
      startTop: 0,
    };

    this.setupHandles();
    this.setupListeners();
  }

  private setupHandles(): void {
    const handles = this.options.handles || [];

    handles.forEach((handle) => {
      const handleElement = document.createElement('div');
      handleElement.className = `resize-handle resize-handle-${handle}`;
      handleElement.dataset.handle = handle;

      // Set cursor for handle
      const cursors: Record<ResizeHandle, string> = {
        n: 'ns-resize',
        s: 'ns-resize',
        e: 'ew-resize',
        w: 'ew-resize',
        ne: 'nesw-resize',
        sw: 'nesw-resize',
        nw: 'nwse-resize',
        se: 'nwse-resize',
      };

      handleElement.style.cursor = cursors[handle];

      this.element.appendChild(handleElement);
      this.handleElements.set(handle, handleElement);
    });

    // Add styles
    this.addHandleStyles();
  }

  private addHandleStyles(): void {
    const style = document.createElement('style');
    style.textContent = `
      .resize-handle {
        position: absolute;
        z-index: 10;
      }

      .resize-handle-n, .resize-handle-s {
        left: 0;
        right: 0;
        height: 8px;
      }

      .resize-handle-n { top: -4px; }
      .resize-handle-s { bottom: -4px; }

      .resize-handle-e, .resize-handle-w {
        top: 0;
        bottom: 0;
        width: 8px;
      }

      .resize-handle-e { right: -4px; }
      .resize-handle-w { left: -4px; }

      .resize-handle-ne, .resize-handle-nw,
      .resize-handle-se, .resize-handle-sw {
        width: 12px;
        height: 12px;
      }

      .resize-handle-ne { top: -6px; right: -6px; }
      .resize-handle-nw { top: -6px; left: -6px; }
      .resize-handle-se { bottom: -6px; right: -6px; }
      .resize-handle-sw { bottom: -6px; left: -6px; }
    `;

    if (!document.getElementById('resize-handle-styles')) {
      style.id = 'resize-handle-styles';
      document.head.appendChild(style);
    }
  }

  private setupListeners(): void {
    // Add pointer down listeners to handles
    this.handleElements.forEach((handleElement, handle) => {
      const handlePointerDown = (e: PointerEvent) => {
        if (this.options.disabled) return;

        e.preventDefault();
        e.stopPropagation();

        this.startResize(e, handle);
      };

      handleElement.addEventListener('pointerdown', handlePointerDown);
      this.unsubscribers.push(() => {
        handleElement.removeEventListener('pointerdown', handlePointerDown);
      });
    });

    // Subscribe to pointer manager
    const unsubMove = pointerManager.on('move', this.handleResize.bind(this));
    const unsubUp = pointerManager.on('up', this.endResize.bind(this));
    const unsubCancel = pointerManager.on('cancel', this.endResize.bind(this));

    this.unsubscribers.push(unsubMove, unsubUp, unsubCancel);
  }

  private startResize(e: PointerEvent, handle: ResizeHandle): void {
    const rect = this.element.getBoundingClientRect();

    this.state.isResizing = true;
    this.state.handle = handle;
    this.state.startX = e.clientX;
    this.state.startY = e.clientY;
    this.state.startWidth = rect.width;
    this.state.startHeight = rect.height;
    this.state.startLeft = rect.left;
    this.state.startTop = rect.top;

    // Call onResizeStart
    if (this.options.onResizeStart) {
      const shouldContinue = this.options.onResizeStart(this.element, {
        width: this.state.startWidth,
        height: this.state.startHeight,
      });

      if (shouldContinue === false) {
        this.state.isResizing = false;
        return;
      }
    }

    this.element.classList.add('resizing');
  }

  private handleResize(data: PointerEventData): void {
    if (!this.state.isResizing || !this.state.handle) return;

    const { position } = data;
    const dx = position.clientX - this.state.startX;
    const dy = position.clientY - this.state.startY;

    let newWidth = this.state.startWidth;
    let newHeight = this.state.startHeight;
    let newLeft = this.state.startLeft;
    let newTop = this.state.startTop;

    const handle = this.state.handle;

    // Calculate new dimensions based on handle
    if (handle.includes('e')) {
      newWidth = this.state.startWidth + dx;
    }
    if (handle.includes('w')) {
      newWidth = this.state.startWidth - dx;
      newLeft = this.state.startLeft + dx;
    }
    if (handle.includes('s')) {
      newHeight = this.state.startHeight + dy;
    }
    if (handle.includes('n')) {
      newHeight = this.state.startHeight - dy;
      newTop = this.state.startTop + dy;
    }

    // Apply aspect ratio
    if (this.options.aspectRatio) {
      if (handle.includes('e') || handle.includes('w')) {
        newHeight = newWidth / this.options.aspectRatio;
      } else {
        newWidth = newHeight * this.options.aspectRatio;
      }
    }

    // Apply grid snapping
    if (this.options.grid) {
      newWidth = Math.round(newWidth / this.options.grid) * this.options.grid;
      newHeight = Math.round(newHeight / this.options.grid) * this.options.grid;
    }

    // Apply size constraints
    newWidth = Math.max(
      this.options.minWidth || 0,
      Math.min(newWidth, this.options.maxWidth || Infinity)
    );
    newHeight = Math.max(
      this.options.minHeight || 0,
      Math.min(newHeight, this.options.maxHeight || Infinity)
    );

    // Apply viewport constraints
    if (this.options.constrainToViewport) {
      newWidth = Math.min(newWidth, window.innerWidth - newLeft);
      newHeight = Math.min(newHeight, window.innerHeight - newTop);
    }

    // Apply parent constraints
    if (this.options.constrainToParent && this.element.parentElement) {
      const parentRect = this.element.parentElement.getBoundingClientRect();
      newWidth = Math.min(newWidth, parentRect.width - (newLeft - parentRect.left));
      newHeight = Math.min(newHeight, parentRect.height - (newTop - parentRect.top));
    }

    // Update element size
    this.element.style.width = `${newWidth}px`;
    this.element.style.height = `${newHeight}px`;

    // Update position if resizing from top or left
    if (handle.includes('w') || handle.includes('n')) {
      if (handle.includes('w')) {
        this.element.style.left = `${newLeft}px`;
      }
      if (handle.includes('n')) {
        this.element.style.top = `${newTop}px`;
      }
    }

    // Call onResize callback
    if (this.options.onResize) {
      this.options.onResize(this.element, {
        width: newWidth,
        height: newHeight,
        left: newLeft,
        top: newTop,
      });
    }
  }

  private endResize(data: PointerEventData): void {
    if (!this.state.isResizing) return;

    this.state.isResizing = false;

    this.element.classList.remove('resizing');

    // Get final size
    const rect = this.element.getBoundingClientRect();

    // Call onResizeEnd
    if (this.options.onResizeEnd) {
      this.options.onResizeEnd(this.element, {
        width: rect.width,
        height: rect.height,
        left: rect.left,
        top: rect.top,
      });
    }

    this.state.handle = null;
  }

  /**
   * Get current state
   */
  public getState(): ResizeState {
    return { ...this.state };
  }

  /**
   * Update options
   */
  public setOptions(options: Partial<ResizeOptions>): void {
    this.options = { ...this.options, ...options };
  }

  /**
   * Enable resizing
   */
  public enable(): void {
    this.setOptions({ disabled: false });
    this.handleElements.forEach((el) => {
      el.style.display = '';
    });
  }

  /**
   * Disable resizing
   */
  public disable(): void {
    this.setOptions({ disabled: true });
    this.handleElements.forEach((el) => {
      el.style.display = 'none';
    });
  }

  /**
   * Set element size programmatically
   */
  public setSize(width: number, height: number): void {
    this.element.style.width = `${width}px`;
    this.element.style.height = `${height}px`;
  }

  /**
   * Get element size
   */
  public getSize(): Size {
    const rect = this.element.getBoundingClientRect();
    return {
      width: rect.width,
      height: rect.height,
    };
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.unsubscribers.forEach((unsub) => unsub());
    this.unsubscribers = [];
    this.handleElements.forEach((el) => el.remove());
    this.handleElements.clear();
    this.element.classList.remove('resizing');
  }
}

/**
 * Make an element resizable
 */
export function makeResizable(
  element: HTMLElement,
  options: ResizeOptions = {}
): Resizable {
  return new Resizable(element, options);
}
