/**
 * Cache Manager
 *
 * Coordinates multi-layer caching (Memory → IndexedDB → Network).
 * Includes automatic precomputation system.
 */

import type { CachedAnalysis, CacheKey, CacheStats, CacheResult } from './types';
import { MemoryCache } from './memory';
import { IndexedDBCache } from './indexeddb';
import { generateCacheKey } from './utils';
import { initPrecompute, getPrecomputeManager } from '../precompute';

export class CacheManager {
  private memoryCache: MemoryCache;
  private indexedDBCache: IndexedDBCache;
  private stats: CacheStats;
  private initialized: boolean = false;

  constructor(memoryCacheSize: number = 1000) {
    this.memoryCache = new MemoryCache(memoryCacheSize);
    this.indexedDBCache = new IndexedDBCache();
    this.stats = {
      memoryHits: 0,
      memoryMisses: 0,
      indexedDBHits: 0,
      indexedDBMisses: 0,
      networkCalls: 0,
      totalQueries: 0,
    };
  }

  /**
   * Initialize cache system
   */
  async init(): Promise<void> {
    if (this.initialized) {
      return;
    }

    console.log('[CACHE MANAGER] Initializing cache layers...');

    try {
      await this.indexedDBCache.init();
      this.initialized = true;
      initPrecompute(this);
    } catch (error) {
      console.warn('[CACHE MANAGER] Init error, falling back to memory-only:', error);
      this.initialized = true;
    }
  }

  /**
   * Get cached analysis (cascading lookup)
   */
  async get(params: CacheKey): Promise<CacheResult> {
    const key = generateCacheKey(params);
    const queryStart = performance.now();
    this.stats.totalQueries++;

    // Step 1: Check memory cache
    const memoryResult = this.memoryCache.get(key);
    if (memoryResult) {
      this.stats.memoryHits++;
      return { data: memoryResult, source: 'memory', duration: performance.now() - queryStart };
    }
    this.stats.memoryMisses++;

    // Step 2: Check IndexedDB cache
    const indexedDBResult = await this.indexedDBCache.get(key);
    if (indexedDBResult) {
      this.stats.indexedDBHits++;
      this.memoryCache.set(key, indexedDBResult);
      return { data: indexedDBResult, source: 'indexeddb', duration: performance.now() - queryStart };
    }
    this.stats.indexedDBMisses++;

    return { data: null, source: null, duration: performance.now() - queryStart };
  }

  /**
   * Store analysis in cache (saves to both layers)
   */
  async set(params: CacheKey, value: CachedAnalysis): Promise<void> {
    const key = generateCacheKey(params);
    this.memoryCache.set(key, value);
    await this.indexedDBCache.set(key, value);
  }

  /**
   * Record a network call (for statistics)
   */
  recordNetworkCall(): void {
    this.stats.networkCalls++;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Get detailed statistics including cache sizes
   */
  async getDetailedStats(): Promise<{
    stats: CacheStats;
    memory: { size: number; maxSize: number; utilizationPercent: number };
    indexedDB: { count: number; estimatedSize: number };
    hitRate: {
      overall: number;
      memory: number;
      indexedDB: number;
    };
  }> {
    const memoryStats = this.memoryCache.getStats();
    const indexedDBStats = await this.indexedDBCache.getStats();

    const totalHits = this.stats.memoryHits + this.stats.indexedDBHits;
    const totalQueries = this.stats.totalQueries;

    return {
      stats: this.stats,
      memory: memoryStats,
      indexedDB: indexedDBStats,
      hitRate: {
        overall: totalQueries > 0 ? (totalHits / totalQueries) * 100 : 0,
        memory: totalQueries > 0 ? (this.stats.memoryHits / totalQueries) * 100 : 0,
        indexedDB: totalQueries > 0 ? (this.stats.indexedDBHits / totalQueries) * 100 : 0,
      },
    };
  }

  /**
   * Print detailed statistics to console
   */
  async printStats(): Promise<void> {
    const stats = await this.getDetailedStats();

    console.log('========================================');
    console.log('CACHE STATISTICS');
    console.log('========================================');
    console.log('Query Stats:');
    console.log(`  Total Queries: ${stats.stats.totalQueries}`);
    console.log(`  Memory Hits: ${stats.stats.memoryHits}`);
    console.log(`  IndexedDB Hits: ${stats.stats.indexedDBHits}`);
    console.log(`  Network Calls: ${stats.stats.networkCalls}`);
    console.log('');
    console.log('Hit Rates:');
    console.log(`  Overall: ${stats.hitRate.overall.toFixed(1)}%`);
    console.log(`  Memory: ${stats.hitRate.memory.toFixed(1)}%`);
    console.log(`  IndexedDB: ${stats.hitRate.indexedDB.toFixed(1)}%`);
    console.log('');
    console.log('Cache Sizes:');
    console.log(`  Memory: ${stats.memory.size}/${stats.memory.maxSize} (${stats.memory.utilizationPercent.toFixed(1)}%)`);
    console.log(`  IndexedDB: ${stats.indexedDB.count} entries (~${(stats.indexedDB.estimatedSize / 1024).toFixed(1)}KB)`);
    console.log('========================================');
  }

  /**
   * Clear all caches
   */
  async clear(): Promise<void> {
    this.memoryCache.clear();
    await this.indexedDBCache.clear();
  }

  /**
   * Cleanup old IndexedDB entries
   */
  async cleanup(olderThanDays: number = 30): Promise<number> {
    return await this.indexedDBCache.cleanup(olderThanDays);
  }

  // ========== Precompute Helper Methods ==========

  /**
   * Trigger precomputation for a position
   * Called after user requests analysis
   */
  async triggerPrecompute(
    params: CacheKey,
    result: { lines: any[]; source?: string }
  ): Promise<void> {
    try {
      const precomputeManager = getPrecomputeManager();
      await precomputeManager.trigger(
        params.fen,
        params.depth,
        params.multipv,
        result
      );
    } catch (error) {
      console.error('[CACHE MANAGER] Precompute trigger failed:', error);
    }
  }

  /**
   * Check if key exists in memory cache (for precompute)
   */
  hasMemory(key: string): boolean {
    return this.memoryCache.get(key) !== null;
  }

  /**
   * Get from IndexedDB only (for precompute)
   */
  async getIndexedDB(key: string): Promise<CachedAnalysis | null> {
    return await this.indexedDBCache.get(key);
  }

  /**
   * Set memory cache (for precompute promotion)
   */
  setMemory(key: string, value: CachedAnalysis): void {
    this.memoryCache.set(key, value);
  }

  /**
   * Set IndexedDB cache (for precompute)
   */
  async setIndexedDB(key: string, value: CachedAnalysis): Promise<void> {
    await this.indexedDBCache.set(key, value);
  }

  /**
   * Get memory cache size
   */
  getMemorySize(): number {
    return this.memoryCache.size();
  }
}
