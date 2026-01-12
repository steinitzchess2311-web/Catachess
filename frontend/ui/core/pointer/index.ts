/**
 * Pointer Module - Unified pointer event handling
 *
 * Provides cross-device pointer event management with touch/mouse support.
 * Handles pointer capture, movement tracking, and gesture detection.
 */

export interface PointerPosition {
  x: number;
  y: number;
  clientX: number;
  clientY: number;
  pageX: number;
  pageY: number;
}

export interface PointerEventData {
  position: PointerPosition;
  target: EventTarget | null;
  timestamp: number;
  type: 'down' | 'move' | 'up' | 'cancel';
  button?: number;
  touches?: number;
}

export type PointerCallback = (event: PointerEventData) => void;

/**
 * Pointer event manager
 */
export class PointerManager {
  private listeners: Map<string, Set<PointerCallback>> = new Map();
  private isPointerDown = false;
  private startPosition: PointerPosition | null = null;
  private currentPosition: PointerPosition | null = null;
  private capturedElement: HTMLElement | null = null;

  constructor() {
    this.setupListeners();
  }

  private setupListeners(): void {
    // Use pointer events for unified touch/mouse handling
    document.addEventListener('pointerdown', this.handlePointerDown.bind(this));
    document.addEventListener('pointermove', this.handlePointerMove.bind(this));
    document.addEventListener('pointerup', this.handlePointerUp.bind(this));
    document.addEventListener('pointercancel', this.handlePointerCancel.bind(this));
  }

  private extractPosition(event: PointerEvent): PointerPosition {
    return {
      x: event.clientX,
      y: event.clientY,
      clientX: event.clientX,
      clientY: event.clientY,
      pageX: event.pageX,
      pageY: event.pageY,
    };
  }

  private handlePointerDown(event: PointerEvent): void {
    this.isPointerDown = true;
    this.startPosition = this.extractPosition(event);
    this.currentPosition = this.startPosition;

    const eventData: PointerEventData = {
      position: this.startPosition,
      target: event.target,
      timestamp: Date.now(),
      type: 'down',
      button: event.button,
    };

    this.emit('down', eventData);
  }

  private handlePointerMove(event: PointerEvent): void {
    this.currentPosition = this.extractPosition(event);

    if (this.isPointerDown) {
      const eventData: PointerEventData = {
        position: this.currentPosition,
        target: event.target,
        timestamp: Date.now(),
        type: 'move',
      };

      this.emit('move', eventData);
    }
  }

  private handlePointerUp(event: PointerEvent): void {
    if (!this.isPointerDown) return;

    this.isPointerDown = false;
    const position = this.extractPosition(event);

    const eventData: PointerEventData = {
      position,
      target: event.target,
      timestamp: Date.now(),
      type: 'up',
      button: event.button,
    };

    this.emit('up', eventData);

    // Reset state
    this.startPosition = null;
    this.currentPosition = null;
    this.releaseCapturedElement();
  }

  private handlePointerCancel(event: PointerEvent): void {
    if (!this.isPointerDown) return;

    this.isPointerDown = false;
    const position = this.extractPosition(event);

    const eventData: PointerEventData = {
      position,
      target: event.target,
      timestamp: Date.now(),
      type: 'cancel',
    };

    this.emit('cancel', eventData);

    // Reset state
    this.startPosition = null;
    this.currentPosition = null;
    this.releaseCapturedElement();
  }

  /**
   * Subscribe to pointer events
   */
  public on(eventType: string, callback: PointerCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    this.listeners.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }

  /**
   * Emit event to all listeners
   */
  private emit(eventType: string, data: PointerEventData): void {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }

  /**
   * Capture pointer events to a specific element
   */
  public captureElement(element: HTMLElement): void {
    this.capturedElement = element;
    element.setPointerCapture(1);
  }

  /**
   * Release pointer capture
   */
  public releaseCapturedElement(): void {
    if (this.capturedElement) {
      try {
        this.capturedElement.releasePointerCapture(1);
      } catch (e) {
        // Ignore errors if pointer is already released
      }
      this.capturedElement = null;
    }
  }

  /**
   * Get current pointer state
   */
  public getState() {
    return {
      isPointerDown: this.isPointerDown,
      startPosition: this.startPosition,
      currentPosition: this.currentPosition,
    };
  }

  /**
   * Calculate distance from start position
   */
  public getDistanceFromStart(): number {
    if (!this.startPosition || !this.currentPosition) return 0;

    const dx = this.currentPosition.x - this.startPosition.x;
    const dy = this.currentPosition.y - this.startPosition.y;

    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Calculate delta from start position
   */
  public getDeltaFromStart(): { dx: number; dy: number } {
    if (!this.startPosition || !this.currentPosition) {
      return { dx: 0, dy: 0 };
    }

    return {
      dx: this.currentPosition.x - this.startPosition.x,
      dy: this.currentPosition.y - this.startPosition.y,
    };
  }

  /**
   * Cleanup and remove all listeners
   */
  public destroy(): void {
    this.listeners.clear();
    this.isPointerDown = false;
    this.startPosition = null;
    this.currentPosition = null;
    this.releaseCapturedElement();
  }
}

// Global singleton instance
export const pointerManager = new PointerManager();
