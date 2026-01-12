/**
 * Drag Module - Element dragging functionality
 *
 * Provides drag-and-drop behavior for elements with constraint support,
 * snapping, and smooth interactions.
 */

import { pointerManager, PointerEventData } from '../pointer';
import { focusManager } from '../focus';

export interface DragOptions {
  handle?: HTMLElement | string; // Drag handle element or selector
  constrainToParent?: boolean; // Constrain to parent bounds
  constrainToViewport?: boolean; // Constrain to viewport
  grid?: number; // Snap to grid
  axis?: 'x' | 'y' | 'both'; // Limit dragging to specific axis
  onDragStart?: (element: HTMLElement, position: { x: number; y: number }) => boolean | void;
  onDrag?: (element: HTMLElement, position: { x: number; y: number }) => void;
  onDragEnd?: (element: HTMLElement, position: { x: number; y: number }) => void;
  disabled?: boolean;
}

export interface DragState {
  isDragging: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  offsetX: number;
  offsetY: number;
}

/**
 * Draggable element controller
 */
export class Draggable {
  private element: HTMLElement;
  private options: DragOptions;
  private state: DragState;
  private handle: HTMLElement;
  private unsubscribers: (() => void)[] = [];
  private boundingElement: HTMLElement | null = null;

  constructor(element: HTMLElement, options: DragOptions = {}) {
    this.element = element;
    this.options = options;

    // Initialize state
    this.state = {
      isDragging: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      offsetX: 0,
      offsetY: 0,
    };

    // Determine drag handle
    if (options.handle) {
      if (typeof options.handle === 'string') {
        const handleElement = element.querySelector(options.handle) as HTMLElement;
        this.handle = handleElement || element;
      } else {
        this.handle = options.handle;
      }
    } else {
      this.handle = element;
    }

    // Determine bounding element
    if (options.constrainToParent) {
      this.boundingElement = element.parentElement;
    }

    this.setupListeners();
  }

  private setupListeners(): void {
    // Handle pointer down on drag handle
    const handlePointerDown = (e: PointerEvent) => {
      if (this.options.disabled) return;

      // Check if click is on handle
      if (!this.handle.contains(e.target as Node)) return;

      e.preventDefault();
      e.stopPropagation();

      this.startDrag(e);

      // Focus the element when starting drag
      const id = this.element.getAttribute('data-focus-id');
      if (id) {
        focusManager.focus(id);
      }
    };

    this.handle.addEventListener('pointerdown', handlePointerDown);
    this.unsubscribers.push(() => {
      this.handle.removeEventListener('pointerdown', handlePointerDown);
    });

    // Add cursor style to handle
    this.handle.style.cursor = 'move';

    // Subscribe to pointer manager events
    const unsubMove = pointerManager.on('move', this.handleDrag.bind(this));
    const unsubUp = pointerManager.on('up', this.endDrag.bind(this));
    const unsubCancel = pointerManager.on('cancel', this.endDrag.bind(this));

    this.unsubscribers.push(unsubMove, unsubUp, unsubCancel);
  }

  private startDrag(e: PointerEvent): void {
    // Get current element position
    const rect = this.element.getBoundingClientRect();

    this.state.isDragging = true;
    this.state.startX = e.clientX;
    this.state.startY = e.clientY;
    this.state.offsetX = e.clientX - rect.left;
    this.state.offsetY = e.clientY - rect.top;
    this.state.currentX = rect.left;
    this.state.currentY = rect.top;

    // Call onDragStart callback
    if (this.options.onDragStart) {
      const shouldContinue = this.options.onDragStart(this.element, {
        x: this.state.currentX,
        y: this.state.currentY,
      });

      // Allow callback to cancel drag
      if (shouldContinue === false) {
        this.state.isDragging = false;
        return;
      }
    }

    // Add dragging class
    this.element.classList.add('dragging');

    // Set position to absolute if not already
    if (getComputedStyle(this.element).position === 'static') {
      this.element.style.position = 'absolute';
    }
  }

  private handleDrag(data: PointerEventData): void {
    if (!this.state.isDragging) return;

    const { position } = data;
    let newX = position.clientX - this.state.offsetX;
    let newY = position.clientY - this.state.offsetY;

    // Apply axis constraint
    if (this.options.axis === 'x') {
      newY = this.state.currentY;
    } else if (this.options.axis === 'y') {
      newX = this.state.currentX;
    }

    // Apply grid snapping
    if (this.options.grid) {
      newX = Math.round(newX / this.options.grid) * this.options.grid;
      newY = Math.round(newY / this.options.grid) * this.options.grid;
    }

    // Apply constraints
    if (this.options.constrainToViewport) {
      const rect = this.element.getBoundingClientRect();
      newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width));
      newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height));
    }

    if (this.options.constrainToParent && this.boundingElement) {
      const parentRect = this.boundingElement.getBoundingClientRect();
      const rect = this.element.getBoundingClientRect();
      newX = Math.max(parentRect.left, Math.min(newX, parentRect.right - rect.width));
      newY = Math.max(parentRect.top, Math.min(newY, parentRect.bottom - rect.height));
    }

    // Update position
    this.state.currentX = newX;
    this.state.currentY = newY;

    this.element.style.left = `${newX}px`;
    this.element.style.top = `${newY}px`;

    // Call onDrag callback
    if (this.options.onDrag) {
      this.options.onDrag(this.element, {
        x: newX,
        y: newY,
      });
    }
  }

  private endDrag(data: PointerEventData): void {
    if (!this.state.isDragging) return;

    this.state.isDragging = false;

    // Remove dragging class
    this.element.classList.remove('dragging');

    // Call onDragEnd callback
    if (this.options.onDragEnd) {
      this.options.onDragEnd(this.element, {
        x: this.state.currentX,
        y: this.state.currentY,
      });
    }
  }

  /**
   * Get current drag state
   */
  public getState(): DragState {
    return { ...this.state };
  }

  /**
   * Update options
   */
  public setOptions(options: Partial<DragOptions>): void {
    this.options = { ...this.options, ...options };

    if (options.disabled !== undefined) {
      this.handle.style.cursor = options.disabled ? 'default' : 'move';
    }
  }

  /**
   * Enable dragging
   */
  public enable(): void {
    this.setOptions({ disabled: false });
  }

  /**
   * Disable dragging
   */
  public disable(): void {
    this.setOptions({ disabled: true });
  }

  /**
   * Set element position programmatically
   */
  public setPosition(x: number, y: number): void {
    this.state.currentX = x;
    this.state.currentY = y;
    this.element.style.left = `${x}px`;
    this.element.style.top = `${y}px`;
  }

  /**
   * Get element position
   */
  public getPosition(): { x: number; y: number } {
    return {
      x: this.state.currentX,
      y: this.state.currentY,
    };
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.unsubscribers.forEach((unsub) => unsub());
    this.unsubscribers = [];
    this.element.classList.remove('dragging');
    this.handle.style.cursor = '';
  }
}

/**
 * Make an element draggable
 */
export function makeDraggable(
  element: HTMLElement,
  options: DragOptions = {}
): Draggable {
  return new Draggable(element, options);
}
