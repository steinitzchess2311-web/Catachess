/**
 * Created at: 2026-07-08 22:36 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-08 22:36 EDT
 * Last Modified by: Codex
 *
 * Behavior Engine - AI state machine for cat behaviors
 */

import type { CatState } from '../types';

export interface BehaviorConfig {
  idleDuration: [number, number];
  walkDuration: [number, number];
  climbDuration: [number, number];
  sitDuration: [number, number];
  sleepDuration: [number, number];
  playDuration: [number, number];
  transitionDelay: number;
}

interface StateTransition {
  state: CatState;
  duration: number;
  timestamp: number;
}

export class BehaviorEngine {
  private currentState: CatState = 'idle';
  private stateStartTime: number = Date.now();
  private nextTransition: StateTransition | null = null;
  private timeoutId: number | null = null;
  private interactionTimeoutId: number | null = null;
  private readonly config: BehaviorConfig;

  constructor(config: Partial<BehaviorConfig> = {}) {
    this.config = {
      idleDuration: config.idleDuration ?? [600000, 1200000],   // 10-20分钟
      walkDuration: config.walkDuration ?? [30000, 60000],      // 30秒-1分钟，沿着地面慢慢走
      climbDuration: config.climbDuration ?? [20000, 40000],    // 20-40秒，爬墙
      sitDuration: config.sitDuration ?? [120000, 300000],      // 2-5分钟
      sleepDuration: config.sleepDuration ?? [180000, 600000],  // 3-10分钟
      playDuration: config.playDuration ?? [5000, 10000],       // 5-10秒
      transitionDelay: config.transitionDelay ?? 500,
    };
  }

  /**
   * Get current state
   */
  getState(): CatState {
    return this.currentState;
  }

  /**
   * Start autonomous behavior
   */
  start(onStateChange: (state: CatState) => void): void {
    this.stop();
    this.scheduleNextTransition(onStateChange);
  }

  /**
   * Stop autonomous behavior
   */
  stop(): void {
    if (this.timeoutId !== null) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    if (this.interactionTimeoutId !== null) {
      clearTimeout(this.interactionTimeoutId);
      this.interactionTimeoutId = null;
    }
    this.nextTransition = null;
  }

  /**
   * Force transition to specific state
   */
  transitionTo(state: CatState, onStateChange: (state: CatState) => void): void {
    this.stop();
    this.currentState = state;
    this.stateStartTime = Date.now();
    onStateChange(state);
    this.scheduleNextTransition(onStateChange);
  }

  /**
   * Handle user interaction (click)
   * Returns true if fall animation should be triggered
   */
  handleInteraction(onStateChange: (state: CatState) => void): boolean {
    if (this.currentState === 'climb') {
      // Clicking while climbing causes cat to fall
      this.stop();
      return true;  // Trigger fall animation
    } else if (this.currentState === 'sleep') {
      this.transitionTo('idle', onStateChange);
      return false;
    } else if (this.currentState === 'idle') {
      this.transitionTo('play', onStateChange);
      this.interactionTimeoutId = window.setTimeout(() => {
        this.interactionTimeoutId = null;
        this.transitionTo('idle', onStateChange);
      }, 5000);
      return false;
    }
    return false;
  }

  /**
   * Schedule next state transition
   */
  private scheduleNextTransition(onStateChange: (state: CatState) => void): void {
    const nextState = this.determineNextState();
    const duration = this.getStateDuration(this.currentState);

    this.timeoutId = window.setTimeout(() => {
      this.currentState = nextState;
      this.stateStartTime = Date.now();
      onStateChange(nextState);
      this.scheduleNextTransition(onStateChange);
    }, duration);
  }

  /**
   * Determine next logical state
   */
  private determineNextState(): CatState {
    const weights = this.getStateWeights();
    const random = Math.random();
    let cumulative = 0;

    for (const [state, weight] of Object.entries(weights)) {
      cumulative += weight;
      if (random <= cumulative) {
        return state as CatState;
      }
    }

    return 'idle';
  }

  /**
   * Get state transition weights based on current state
   */
  private getStateWeights(): Record<CatState, number> {
    switch (this.currentState) {
      case 'idle':
        return { walk: 0.5, climb: 0.15, sit: 0.2, sleep: 0.1, play: 0.05, idle: 0, fall: 0 };
      case 'walk':
        return { idle: 0.6, climb: 0.15, sit: 0.15, sleep: 0.1, play: 0, walk: 0, fall: 0 };
      case 'climb':
        return { idle: 0.6, walk: 0.3, sit: 0.1, sleep: 0, play: 0, climb: 0, fall: 0 };
      case 'sit':
        return { idle: 0.5, walk: 0.3, climb: 0.1, sleep: 0.1, play: 0, sit: 0, fall: 0 };
      case 'sleep':
        return { idle: 0.8, walk: 0.1, sit: 0.1, climb: 0, play: 0, sleep: 0, fall: 0 };
      case 'play':
        return { idle: 0.6, walk: 0.3, climb: 0.1, sit: 0, sleep: 0, play: 0, fall: 0 };
      case 'fall':
        return { idle: 1, walk: 0, climb: 0, sit: 0, sleep: 0, play: 0, fall: 0 };
      default:
        return { idle: 1, walk: 0, climb: 0, sit: 0, sleep: 0, play: 0, fall: 0 };
    }
  }

  /**
   * Get duration for current state
   */
  private getStateDuration(state: CatState): number {
    const [min, max] =
      state === 'idle'
        ? this.config.idleDuration
        : state === 'walk'
          ? this.config.walkDuration
          : state === 'climb'
            ? this.config.climbDuration
            : state === 'sit'
              ? this.config.sitDuration
              : state === 'sleep'
                ? this.config.sleepDuration
                : state === 'play'
                  ? this.config.playDuration
                  : [1000, 2000];  // fall or other states

    return min + Math.random() * (max - min);
  }

  /**
   * Cleanup
   */
  destroy(): void {
    this.stop();
  }
}
