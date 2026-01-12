/**
 * Scroll Module - Smooth scrolling and scroll management
 *
 * Provides smooth scrolling, scroll position tracking, and
 * scroll-related utilities for panels and containers.
 */

export interface ScrollOptions {
  behavior?: ScrollBehavior; // 'smooth' | 'auto'
  duration?: number; // Animation duration in ms
  easing?: (t: number) => number; // Easing function
}

export interface ScrollPosition {
  x: number;
  y: number;
  maxX: number;
  maxY: number;
  percentX: number;
  percentY: number;
}

/**
 * Easing functions
 */
export const easings = {
  linear: (t: number) => t,
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => --t * t * t + 1,
  easeInOutCubic: (t: number) =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
};

/**
 * Scroll controller for an element
 */
export class ScrollController {
  private element: HTMLElement;
  private animationFrame: number | null = null;
  private scrollListeners: Set<(position: ScrollPosition) => void> = new Set();

  constructor(element: HTMLElement) {
    this.element = element;
    this.setupListeners();
  }

  private setupListeners(): void {
    this.element.addEventListener('scroll', this.handleScroll.bind(this));
  }

  private handleScroll(): void {
    const position = this.getScrollPosition();
    this.scrollListeners.forEach((listener) => listener(position));
  }

  /**
   * Get current scroll position with metadata
   */
  public getScrollPosition(): ScrollPosition {
    const x = this.element.scrollLeft;
    const y = this.element.scrollTop;
    const maxX = this.element.scrollWidth - this.element.clientWidth;
    const maxY = this.element.scrollHeight - this.element.clientHeight;

    return {
      x,
      y,
      maxX,
      maxY,
      percentX: maxX > 0 ? x / maxX : 0,
      percentY: maxY > 0 ? y / maxY : 0,
    };
  }

  /**
   * Scroll to position with animation
   */
  public scrollTo(
    x: number,
    y: number,
    options: ScrollOptions = {}
  ): Promise<void> {
    return new Promise((resolve) => {
      // Cancel any ongoing animation
      if (this.animationFrame) {
        cancelAnimationFrame(this.animationFrame);
      }

      const startX = this.element.scrollLeft;
      const startY = this.element.scrollTop;
      const deltaX = x - startX;
      const deltaY = y - startY;

      // If no animation needed
      if (options.behavior === 'auto' || (!deltaX && !deltaY)) {
        this.element.scrollLeft = x;
        this.element.scrollTop = y;
        resolve();
        return;
      }

      const duration = options.duration || 300;
      const easing = options.easing || easings.easeInOutQuad;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easing(progress);

        this.element.scrollLeft = startX + deltaX * easedProgress;
        this.element.scrollTop = startY + deltaY * easedProgress;

        if (progress < 1) {
          this.animationFrame = requestAnimationFrame(animate);
        } else {
          this.animationFrame = null;
          resolve();
        }
      };

      this.animationFrame = requestAnimationFrame(animate);
    });
  }

  /**
   * Scroll by delta amount
   */
  public scrollBy(
    dx: number,
    dy: number,
    options: ScrollOptions = {}
  ): Promise<void> {
    const currentX = this.element.scrollLeft;
    const currentY = this.element.scrollTop;
    return this.scrollTo(currentX + dx, currentY + dy, options);
  }

  /**
   * Scroll to top
   */
  public scrollToTop(options: ScrollOptions = {}): Promise<void> {
    return this.scrollTo(this.element.scrollLeft, 0, options);
  }

  /**
   * Scroll to bottom
   */
  public scrollToBottom(options: ScrollOptions = {}): Promise<void> {
    const maxY = this.element.scrollHeight - this.element.clientHeight;
    return this.scrollTo(this.element.scrollLeft, maxY, options);
  }

  /**
   * Scroll to left
   */
  public scrollToLeft(options: ScrollOptions = {}): Promise<void> {
    return this.scrollTo(0, this.element.scrollTop, options);
  }

  /**
   * Scroll to right
   */
  public scrollToRight(options: ScrollOptions = {}): Promise<void> {
    const maxX = this.element.scrollWidth - this.element.clientWidth;
    return this.scrollTo(maxX, this.element.scrollTop, options);
  }

  /**
   * Scroll element into view
   */
  public scrollIntoView(
    target: HTMLElement,
    options: ScrollOptions & { block?: 'start' | 'center' | 'end' } = {}
  ): Promise<void> {
    const containerRect = this.element.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();

    let targetY = this.element.scrollTop + (targetRect.top - containerRect.top);

    // Adjust based on block option
    if (options.block === 'center') {
      targetY -= (containerRect.height - targetRect.height) / 2;
    } else if (options.block === 'end') {
      targetY -= containerRect.height - targetRect.height;
    }

    return this.scrollTo(this.element.scrollLeft, targetY, options);
  }

  /**
   * Check if element is scrollable
   */
  public isScrollable(): { x: boolean; y: boolean } {
    return {
      x: this.element.scrollWidth > this.element.clientWidth,
      y: this.element.scrollHeight > this.element.clientHeight,
    };
  }

  /**
   * Check if scrolled to top
   */
  public isAtTop(): boolean {
    return this.element.scrollTop === 0;
  }

  /**
   * Check if scrolled to bottom
   */
  public isAtBottom(): boolean {
    const maxY = this.element.scrollHeight - this.element.clientHeight;
    return Math.abs(this.element.scrollTop - maxY) < 1;
  }

  /**
   * Check if scrolled to left
   */
  public isAtLeft(): boolean {
    return this.element.scrollLeft === 0;
  }

  /**
   * Check if scrolled to right
   */
  public isAtRight(): boolean {
    const maxX = this.element.scrollWidth - this.element.clientWidth;
    return Math.abs(this.element.scrollLeft - maxX) < 1;
  }

  /**
   * Subscribe to scroll events
   */
  public onScroll(callback: (position: ScrollPosition) => void): () => void {
    this.scrollListeners.add(callback);

    // Return unsubscribe function
    return () => {
      this.scrollListeners.delete(callback);
    };
  }

  /**
   * Stop any ongoing scroll animation
   */
  public stop(): void {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.stop();
    this.scrollListeners.clear();
  }
}

/**
 * Create scroll controller for element
 */
export function createScrollController(element: HTMLElement): ScrollController {
  return new ScrollController(element);
}

/**
 * Utility: Smoothly scroll window to position
 */
export function scrollWindowTo(
  x: number,
  y: number,
  options: ScrollOptions = {}
): Promise<void> {
  return new Promise((resolve) => {
    const startX = window.scrollX;
    const startY = window.scrollY;
    const deltaX = x - startX;
    const deltaY = y - startY;

    if (options.behavior === 'auto' || (!deltaX && !deltaY)) {
      window.scrollTo(x, y);
      resolve();
      return;
    }

    const duration = options.duration || 300;
    const easing = options.easing || easings.easeInOutQuad;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easing(progress);

      window.scrollTo(
        startX + deltaX * easedProgress,
        startY + deltaY * easedProgress
      );

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        resolve();
      }
    };

    requestAnimationFrame(animate);
  });
}
