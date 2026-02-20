/**
 * PrecomputeManager — background position precomputation.
 *
 * After each engine result, queues neighboring positions (horizontal = top-N
 * lines, vertical = 1-2 moves deep) so they are ready before the user moves.
 * All logging is DEV-only to keep production consoles clean.
 */

import { analyzeWithFallback } from '../client';
import { generateCacheKey } from '../cache/utils';
import type { EngineAnalysis } from '../types';
import { MoveParser } from './move-parser';
import { PriorityQueue } from './queue';
import { StatsTracker } from './stats';
import { PrecomputeStorage } from './storage';
import type { PrecomputeTask, PrecomputeSettings, PrecomputeStatus } from './types';

// DEV-only logger — compiled away in production builds
const log = (...args: unknown[]) => {
  if (import.meta.env.DEV) console.log('[PRECOMPUTE]', ...args);
};

const DEFAULT_SETTINGS: PrecomputeSettings = {
  enabled: true,
  horizontalDepth: 5,
  verticalDepth: 2,
  delayMs: 100,
  maxConcurrent: 1,
};

export class PrecomputeManager {
  private settings: PrecomputeSettings = DEFAULT_SETTINGS;
  private queue: PriorityQueue = new PriorityQueue();
  private stats: StatsTracker = new StatsTracker();

  private currentSessionController: AbortController | null = null;
  private taskControllers: Map<string, AbortController> = new Map();

  private running = false;
  private runningTasks = 0;
  private currentTask: PrecomputeTask | null = null;
  private cacheManager: any = null;

  constructor() {
    log('Initializing | Settings:', JSON.stringify(DEFAULT_SETTINGS));
  }

  init(cacheManager: any): void {
    this.cacheManager = cacheManager;
    this.currentSessionController = new AbortController();
    log('✓ Initialized with cache manager');
  }

  async trigger(fen: string, depth: number, multipv: number, result: EngineAnalysis): Promise<void> {
    if (!this.settings.enabled || !this.cacheManager) return;
    log(`Trigger | Lines: ${result.lines.length}`);
    try {
      await this.extractHorizontalTasks(fen, depth, multipv, result);
      await this.extractVerticalTasks(fen, depth, multipv, result);
      this.start();
    } catch (error) {
      console.error('[PRECOMPUTE] Trigger failed:', error);
    }
  }

  private async extractHorizontalTasks(fen: string, depth: number, multipv: number, result: EngineAnalysis): Promise<void> {
    const positions = MoveParser.extractNextPositions(fen, result.lines, this.settings.horizontalDepth);
    log(`Horizontal: ${positions.length} positions`);
    for (const pos of positions) {
      await this.addTask({
        fen: pos.fen, depth, multipv,
        priority: this.calculatePriority(pos.lineIndex, 0),
        fromFEN: fen, move: pos.move, lineIndex: pos.lineIndex, treeDepth: 0,
      });
    }
  }

  private async extractVerticalTasks(fen: string, depth: number, multipv: number, result: EngineAnalysis): Promise<void> {
    if (this.settings.verticalDepth === 0) return;
    let total = 0;
    for (let i = 0; i < Math.min(this.settings.horizontalDepth, result.lines.length); i++) {
      const positions = MoveParser.extractDeepPositions(fen, result.lines[i].pv, this.settings.verticalDepth);
      for (const pos of positions) {
        await this.addTask({
          fen: pos.fen, depth, multipv,
          priority: this.calculatePriority(i, pos.depth),
          fromFEN: pos.fromFEN, move: pos.move, lineIndex: i, treeDepth: pos.depth,
        });
        total++;
      }
    }
    log(`Vertical: ${total} positions`);
  }

  async addTask(params: {
    fen: string; depth: number; multipv: number; priority: number;
    fromFEN: string; move: string; lineIndex: number; treeDepth: number;
  }): Promise<void> {
    const cacheKey = generateCacheKey({ fen: params.fen, depth: params.depth, multipv: params.multipv });
    const should = await PrecomputeStorage.shouldPrecompute(cacheKey, params.fen, params.depth, params.multipv, this.cacheManager, this.queue);
    if (!should) { this.stats.cacheHit(cacheKey); return; }

    const task: PrecomputeTask = {
      id: `${cacheKey}_${Date.now()}`,
      cacheKey,
      fen: params.fen, depth: params.depth, multipv: params.multipv,
      priority: params.priority, fromFEN: params.fromFEN, move: params.move,
      lineIndex: params.lineIndex, treeDepth: params.treeDepth,
      createdAt: Date.now(), status: 'pending', retries: 0,
    };
    if (this.queue.insert(task, params.priority)) this.stats.taskTriggered(task);
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    log(`Starting queue | size: ${this.queue.size()}`);
    setTimeout(() => this.processQueue(), this.settings.delayMs);
  }

  private async processQueue(): Promise<void> {
    while (this.running && this.queue.size() > 0) {
      if (this.runningTasks >= this.settings.maxConcurrent) { await this.waitForSlot(); continue; }
      const task = this.queue.dequeue();
      if (!task) break;
      this.runningTasks++;
      this.currentTask = task;
      this.executeTask(task).finally(() => { this.runningTasks--; this.currentTask = null; });
      await this.delay(this.getTaskDelay(task));
    }
    if (this.queue.size() === 0) {
      log('Queue complete');
      this.stats.printSummary();
      this.running = false;
    }
  }

  private async executeTask(task: PrecomputeTask): Promise<void> {
    const startTime = Date.now();
    try {
      task.status = 'running';
      task.startedAt = Date.now();
      const controller = new AbortController();
      this.taskControllers.set(task.id, controller);

      const shouldRun = await PrecomputeStorage.shouldPrecompute(task.cacheKey, task.fen, task.depth, task.multipv, this.cacheManager, this.queue);
      if (!shouldRun) { task.status = 'completed'; this.stats.cacheHit(task.cacheKey); return; }

      const result = await analyzeWithFallback(task.fen, task.multipv);
      await PrecomputeStorage.storeResult(task, result, this.cacheManager);
      task.status = 'completed';
      task.completedAt = Date.now();
      this.stats.taskCompleted(task, Date.now() - startTime);
      log(`✓ Task done | ${task.move} in ${Date.now() - startTime}ms`);
    } catch (error: any) {
      if (error.name === 'AbortError') {
        task.status = 'cancelled';
        this.stats.taskCancelled(task);
        return;
      }
      task.status = 'failed';
      task.error = error.message;
      this.stats.taskFailed(task, error.message);
      console.error('[PRECOMPUTE] Task failed:', task.move, error.message);
    } finally {
      this.taskControllers.delete(task.id);
    }
  }

  cancelCurrentSession(): void {
    const total = this.queue.size() + this.runningTasks;
    if (total === 0) return;
    this.currentSessionController?.abort();
    this.currentSessionController = new AbortController();
    this.taskControllers.forEach((c) => c.abort());
    this.taskControllers.clear();
    this.queue.clear();
    this.running = false;
    this.runningTasks = 0;
    this.currentTask = null;
    log(`Session cancelled | ${total} tasks removed`);
  }

  updateSettings(settings: Partial<PrecomputeSettings>): void {
    this.settings = { ...this.settings, ...settings };
  }

  getStatus(): PrecomputeStatus {
    return {
      enabled: this.settings.enabled,
      running: this.running,
      queueSize: this.queue.size(),
      completed: this.stats.getStats().completed,
      failed: this.stats.getStats().failed,
      cancelled: this.stats.getStats().cancelled,
      currentTask: this.currentTask
        ? { move: this.currentTask.move, lineIndex: this.currentTask.lineIndex, treeDepth: this.currentTask.treeDepth, elapsedMs: this.currentTask.startedAt ? Date.now() - this.currentTask.startedAt : 0 }
        : undefined,
    };
  }

  getStats() { return this.stats.getStats(); }
  printSummary() { this.stats.printSummary(); }

  private calculatePriority(lineIndex: number, treeDepth: number): number {
    if (treeDepth === 0) return Math.max(60, 100 - lineIndex * 10);
    return Math.max(10, 50 - treeDepth * 10);
  }

  private getTaskDelay(task: PrecomputeTask): number {
    return task.treeDepth === 0 ? 100 : 1000 * task.treeDepth;
  }

  private async waitForSlot(): Promise<void> {
    return new Promise((resolve) => {
      const check = () => this.runningTasks < this.settings.maxConcurrent ? resolve() : setTimeout(check, 100);
      check();
    });
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
