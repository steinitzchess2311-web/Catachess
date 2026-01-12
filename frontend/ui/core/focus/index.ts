/**
 * Focus Module - Window focus and z-index management
 *
 * Manages focus order of multiple panels/windows, avoiding z-index hell.
 * Provides click-to-focus behavior and maintains proper stacking order.
 */

export interface FocusableElement {
  id: string;
  element: HTMLElement;
  order: number;
  zIndex: number;
}

export type FocusChangeCallback = (focusedId: string | null) => void;

/**
 * Focus manager - manages z-index and focus order
 */
export class FocusManager {
  private elements: Map<string, FocusableElement> = new Map();
  private focusOrder: string[] = [];
  private currentFocused: string | null = null;
  private baseZIndex: number = 1000;
  private listeners: Set<FocusChangeCallback> = new Set();

  /**
   * Register an element for focus management
   */
  public register(id: string, element: HTMLElement): () => void {
    if (this.elements.has(id)) {
      console.warn(`Element with id ${id} is already registered`);
      return () => {};
    }

    const focusableElement: FocusableElement = {
      id,
      element,
      order: this.focusOrder.length,
      zIndex: this.baseZIndex + this.focusOrder.length,
    };

    this.elements.set(id, focusableElement);
    this.focusOrder.push(id);

    // Apply initial z-index
    element.style.zIndex = String(focusableElement.zIndex);

    // Add click listener to bring to front
    const clickHandler = (e: MouseEvent) => {
      // Only focus if clicking directly on this element or its descendants
      if (element.contains(e.target as Node)) {
        this.focus(id);
      }
    };

    element.addEventListener('mousedown', clickHandler);
    element.addEventListener('touchstart', clickHandler);

    // Return unregister function
    return () => {
      this.unregister(id);
      element.removeEventListener('mousedown', clickHandler);
      element.removeEventListener('touchstart', clickHandler);
    };
  }

  /**
   * Unregister an element
   */
  public unregister(id: string): void {
    const element = this.elements.get(id);
    if (!element) return;

    this.elements.delete(id);
    this.focusOrder = this.focusOrder.filter((fid) => fid !== id);

    if (this.currentFocused === id) {
      this.currentFocused = null;
      this.notifyListeners();
    }

    // Recompute z-indices for remaining elements
    this.recomputeZIndices();
  }

  /**
   * Focus an element (bring to front)
   */
  public focus(id: string): void {
    const element = this.elements.get(id);
    if (!element) {
      console.warn(`Element with id ${id} is not registered`);
      return;
    }

    // Already focused
    if (this.currentFocused === id) return;

    // Remove from current position in order
    this.focusOrder = this.focusOrder.filter((fid) => fid !== id);

    // Add to end (top of stack)
    this.focusOrder.push(id);

    // Update current focused
    const previousFocused = this.currentFocused;
    this.currentFocused = id;

    // Recompute z-indices
    this.recomputeZIndices();

    // Add focused class
    if (previousFocused) {
      const prevElement = this.elements.get(previousFocused);
      if (prevElement) {
        prevElement.element.classList.remove('focused');
      }
    }

    element.element.classList.add('focused');

    // Notify listeners
    this.notifyListeners();
  }

  /**
   * Blur an element (remove focus)
   */
  public blur(id: string): void {
    const element = this.elements.get(id);
    if (!element) return;

    element.element.classList.remove('focused');

    if (this.currentFocused === id) {
      this.currentFocused = null;
      this.notifyListeners();
    }
  }

  /**
   * Get currently focused element ID
   */
  public getFocused(): string | null {
    return this.currentFocused;
  }

  /**
   * Get all registered element IDs in focus order
   */
  public getFocusOrder(): string[] {
    return [...this.focusOrder];
  }

  /**
   * Bring element to front (same as focus)
   */
  public bringToFront(id: string): void {
    this.focus(id);
  }

  /**
   * Send element to back
   */
  public sendToBack(id: string): void {
    const element = this.elements.get(id);
    if (!element) return;

    // Remove from current position
    this.focusOrder = this.focusOrder.filter((fid) => fid !== id);

    // Add to beginning (bottom of stack)
    this.focusOrder.unshift(id);

    // Recompute z-indices
    this.recomputeZIndices();

    // If this was focused, clear focus
    if (this.currentFocused === id) {
      this.currentFocused = null;
      element.element.classList.remove('focused');
      this.notifyListeners();
    }
  }

  /**
   * Move element forward in z-order
   */
  public moveForward(id: string): void {
    const currentIndex = this.focusOrder.indexOf(id);
    if (currentIndex === -1 || currentIndex === this.focusOrder.length - 1) {
      return; // Already at front or not found
    }

    // Swap with next element
    [this.focusOrder[currentIndex], this.focusOrder[currentIndex + 1]] = [
      this.focusOrder[currentIndex + 1],
      this.focusOrder[currentIndex],
    ];

    this.recomputeZIndices();
  }

  /**
   * Move element backward in z-order
   */
  public moveBackward(id: string): void {
    const currentIndex = this.focusOrder.indexOf(id);
    if (currentIndex <= 0) {
      return; // Already at back or not found
    }

    // Swap with previous element
    [this.focusOrder[currentIndex], this.focusOrder[currentIndex - 1]] = [
      this.focusOrder[currentIndex - 1],
      this.focusOrder[currentIndex],
    ];

    this.recomputeZIndices();
  }

  /**
   * Recompute z-indices based on focus order
   */
  private recomputeZIndices(): void {
    this.focusOrder.forEach((id, index) => {
      const element = this.elements.get(id);
      if (element) {
        const zIndex = this.baseZIndex + index;
        element.zIndex = zIndex;
        element.order = index;
        element.element.style.zIndex = String(zIndex);
      }
    });
  }

  /**
   * Subscribe to focus changes
   */
  public onFocusChange(callback: FocusChangeCallback): () => void {
    this.listeners.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Notify all listeners of focus change
   */
  private notifyListeners(): void {
    this.listeners.forEach((callback) => {
      callback(this.currentFocused);
    });
  }

  /**
   * Set base z-index (minimum z-index for managed elements)
   */
  public setBaseZIndex(baseZIndex: number): void {
    this.baseZIndex = baseZIndex;
    this.recomputeZIndices();
  }

  /**
   * Get element by ID
   */
  public getElement(id: string): FocusableElement | undefined {
    return this.elements.get(id);
  }

  /**
   * Check if element is registered
   */
  public has(id: string): boolean {
    return this.elements.has(id);
  }

  /**
   * Get all registered elements
   */
  public getAllElements(): FocusableElement[] {
    return this.focusOrder
      .map((id) => this.elements.get(id))
      .filter((el): el is FocusableElement => el !== undefined);
  }

  /**
   * Clear all registered elements
   */
  public clear(): void {
    this.elements.forEach((element) => {
      element.element.classList.remove('focused');
    });

    this.elements.clear();
    this.focusOrder = [];
    this.currentFocused = null;
    this.notifyListeners();
  }

  /**
   * Cleanup
   */
  public destroy(): void {
    this.clear();
    this.listeners.clear();
  }
}

// Global singleton instance
export const focusManager = new FocusManager();
