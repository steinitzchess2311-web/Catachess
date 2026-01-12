/**
 * Utils Module - Window management utilities
 *
 * Provides edge snapping, window maximize/restore, and
 * macOS-style window management features.
 */

export interface SnapZone {
  type: 'left' | 'right' | 'top' | 'bottom' | 'topleft' | 'topright' | 'bottomleft' | 'bottomright' | 'maximize';
  rect: DOMRect;
}

export interface WindowState {
  isMaximized: boolean;
  isSnapped: boolean;
  snapZone?: SnapZone['type'];
  savedPosition?: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

/**
 * Edge snapping manager
 */
export class SnapManager {
  private snapThreshold: number = 20; // Distance in pixels to trigger snap
  private edgeMargin: number = 10; // Margin from viewport edge

  constructor(snapThreshold: number = 20) {
    this.snapThreshold = snapThreshold;
  }

  /**
   * Calculate snap zones for the viewport
   */
  public getSnapZones(): SnapZone[] {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const margin = this.edgeMargin;

    return [
      // Left half
      {
        type: 'left',
        rect: new DOMRect(0, 0, vw / 2, vh),
      },
      // Right half
      {
        type: 'right',
        rect: new DOMRect(vw / 2, 0, vw / 2, vh),
      },
      // Top half
      {
        type: 'top',
        rect: new DOMRect(0, 0, vw, vh / 2),
      },
      // Bottom half
      {
        type: 'bottom',
        rect: new DOMRect(0, vh / 2, vw, vh / 2),
      },
      // Top-left quarter
      {
        type: 'topleft',
        rect: new DOMRect(0, 0, vw / 2, vh / 2),
      },
      // Top-right quarter
      {
        type: 'topright',
        rect: new DOMRect(vw / 2, 0, vw / 2, vh / 2),
      },
      // Bottom-left quarter
      {
        type: 'bottomleft',
        rect: new DOMRect(0, vh / 2, vw / 2, vh / 2),
      },
      // Bottom-right quarter
      {
        type: 'bottomright',
        rect: new DOMRect(vw / 2, vh / 2, vw / 2, vh / 2),
      },
      // Maximize (top edge)
      {
        type: 'maximize',
        rect: new DOMRect(0, 0, vw, margin),
      },
    ];
  }

  /**
   * Detect snap zone based on position
   */
  public detectSnapZone(x: number, y: number): SnapZone | null {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const threshold = this.snapThreshold;

    // Check for maximize (dragging to top edge)
    if (y <= threshold) {
      return {
        type: 'maximize',
        rect: new DOMRect(0, 0, vw, vh),
      };
    }

    // Check corners first (they take precedence)
    if (x <= threshold && y <= threshold) {
      return {
        type: 'topleft',
        rect: new DOMRect(0, 0, vw / 2, vh / 2),
      };
    }

    if (x >= vw - threshold && y <= threshold) {
      return {
        type: 'topright',
        rect: new DOMRect(vw / 2, 0, vw / 2, vh / 2),
      };
    }

    if (x <= threshold && y >= vh - threshold) {
      return {
        type: 'bottomleft',
        rect: new DOMRect(0, vh / 2, vw / 2, vh / 2),
      };
    }

    if (x >= vw - threshold && y >= vh - threshold) {
      return {
        type: 'bottomright',
        rect: new DOMRect(vw / 2, vh / 2, vw / 2, vh / 2),
      };
    }

    // Check edges
    if (x <= threshold) {
      return {
        type: 'left',
        rect: new DOMRect(0, 0, vw / 2, vh),
      };
    }

    if (x >= vw - threshold) {
      return {
        type: 'right',
        rect: new DOMRect(vw / 2, 0, vw / 2, vh),
      };
    }

    // Bottom edge doesn't snap by default (can be enabled if needed)

    return null;
  }

  /**
   * Apply snap zone to element
   */
  public applySnapZone(element: HTMLElement, zone: SnapZone): void {
    const rect = zone.rect;
    element.style.left = `${rect.left}px`;
    element.style.top = `${rect.top}px`;
    element.style.width = `${rect.width}px`;
    element.style.height = `${rect.height}px`;
  }

  /**
   * Show snap preview overlay
   */
  public showSnapPreview(zone: SnapZone): HTMLElement {
    // Remove existing preview
    this.hideSnapPreview();

    const preview = document.createElement('div');
    preview.id = 'snap-preview';
    preview.className = 'snap-preview';

    const rect = zone.rect;
    preview.style.cssText = `
      position: fixed;
      left: ${rect.left}px;
      top: ${rect.top}px;
      width: ${rect.width}px;
      height: ${rect.height}px;
      background: rgba(100, 150, 255, 0.2);
      border: 2px solid rgba(100, 150, 255, 0.5);
      pointer-events: none;
      z-index: 999999;
      transition: all 0.1s ease;
    `;

    document.body.appendChild(preview);
    return preview;
  }

  /**
   * Hide snap preview overlay
   */
  public hideSnapPreview(): void {
    const preview = document.getElementById('snap-preview');
    if (preview) {
      preview.remove();
    }
  }

  /**
   * Set snap threshold
   */
  public setSnapThreshold(threshold: number): void {
    this.snapThreshold = threshold;
  }
}

/**
 * Window state manager for maximize/restore
 */
export class WindowStateManager {
  private states: Map<string, WindowState> = new Map();

  /**
   * Save current window state
   */
  private saveState(id: string, element: HTMLElement): void {
    const rect = element.getBoundingClientRect();
    const currentState = this.states.get(id) || {
      isMaximized: false,
      isSnapped: false,
    };

    currentState.savedPosition = {
      left: rect.left,
      top: rect.top,
      width: rect.width,
      height: rect.height,
    };

    this.states.set(id, currentState);
  }

  /**
   * Maximize window
   */
  public maximize(id: string, element: HTMLElement): void {
    const state = this.states.get(id) || {
      isMaximized: false,
      isSnapped: false,
    };

    // Save current position if not already maximized
    if (!state.isMaximized && !state.isSnapped) {
      this.saveState(id, element);
    }

    // Apply maximized state
    element.style.left = '0px';
    element.style.top = '0px';
    element.style.width = `${window.innerWidth}px`;
    element.style.height = `${window.innerHeight}px`;

    state.isMaximized = true;
    state.isSnapped = false;
    element.classList.add('maximized');
    element.classList.remove('snapped');

    this.states.set(id, state);
  }

  /**
   * Restore window to previous state
   */
  public restore(id: string, element: HTMLElement): void {
    const state = this.states.get(id);
    if (!state || !state.savedPosition) {
      return;
    }

    const { left, top, width, height } = state.savedPosition;

    element.style.left = `${left}px`;
    element.style.top = `${top}px`;
    element.style.width = `${width}px`;
    element.style.height = `${height}px`;

    state.isMaximized = false;
    state.isSnapped = false;
    element.classList.remove('maximized', 'snapped');

    this.states.set(id, state);
  }

  /**
   * Toggle maximize/restore
   */
  public toggleMaximize(id: string, element: HTMLElement): void {
    const state = this.states.get(id);

    if (state && (state.isMaximized || state.isSnapped)) {
      this.restore(id, element);
    } else {
      this.maximize(id, element);
    }
  }

  /**
   * Snap window to zone
   */
  public snap(id: string, element: HTMLElement, zone: SnapZone): void {
    const state = this.states.get(id) || {
      isMaximized: false,
      isSnapped: false,
    };

    // Save current position if not already snapped or maximized
    if (!state.isMaximized && !state.isSnapped) {
      this.saveState(id, element);
    }

    // Apply snap zone
    const rect = zone.rect;
    element.style.left = `${rect.left}px`;
    element.style.top = `${rect.top}px`;
    element.style.width = `${rect.width}px`;
    element.style.height = `${rect.height}px`;

    state.isSnapped = true;
    state.isMaximized = zone.type === 'maximize';
    state.snapZone = zone.type;
    element.classList.add('snapped');

    if (zone.type === 'maximize') {
      element.classList.add('maximized');
    } else {
      element.classList.remove('maximized');
    }

    this.states.set(id, state);
  }

  /**
   * Get window state
   */
  public getState(id: string): WindowState | undefined {
    return this.states.get(id);
  }

  /**
   * Check if window is maximized
   */
  public isMaximized(id: string): boolean {
    const state = this.states.get(id);
    return state ? state.isMaximized : false;
  }

  /**
   * Check if window is snapped
   */
  public isSnapped(id: string): boolean {
    const state = this.states.get(id);
    return state ? state.isSnapped : false;
  }

  /**
   * Clear state for window
   */
  public clearState(id: string): void {
    this.states.delete(id);
  }

  /**
   * Clear all states
   */
  public clearAll(): void {
    this.states.clear();
  }
}

// Global singleton instances
export const snapManager = new SnapManager();
export const windowStateManager = new WindowStateManager();

/**
 * Utility: Constrain position to viewport
 */
export function constrainToViewport(
  x: number,
  y: number,
  width: number,
  height: number
): { x: number; y: number } {
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  return {
    x: Math.max(0, Math.min(x, vw - width)),
    y: Math.max(0, Math.min(y, vh - height)),
  };
}

/**
 * Utility: Constrain size to viewport
 */
export function constrainSizeToViewport(
  width: number,
  height: number
): { width: number; height: number } {
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  return {
    width: Math.min(width, vw),
    height: Math.min(height, vh),
  };
}

/**
 * Utility: Check if element is in viewport
 */
export function isInViewport(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= window.innerHeight &&
    rect.right <= window.innerWidth
  );
}

/**
 * Utility: Get center position for element
 */
export function getCenterPosition(
  width: number,
  height: number
): { x: number; y: number } {
  return {
    x: (window.innerWidth - width) / 2,
    y: (window.innerHeight - height) / 2,
  };
}
