// Search and fuzzy matching utilities

import { api } from '../../../assets/api';
import { WorkspaceState } from './types';

export function parseSearch(value: string) {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const lower = trimmed.toLowerCase();
    if (lower.startsWith('folder/')) {
        return { type: 'folder' as const, query: trimmed.slice(7).trim() };
    }
    if (lower.startsWith('study/')) {
        return { type: 'study' as const, query: trimmed.slice(6).trim() };
    }
    return { type: null, query: trimmed };
}

export function levenshtein(a: string, b: string) {
    const m = a.length;
    const n = b.length;
    const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    for (let i = 0; i <= m; i += 1) dp[i][0] = i;
    for (let j = 0; j <= n; j += 1) dp[0][j] = j;
    for (let i = 1; i <= m; i += 1) {
        for (let j = 1; j <= n; j += 1) {
            const cost = a[i - 1] === b[j - 1] ? 0 : 1;
            dp[i][j] = Math.min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            );
        }
    }
    return dp[m][n];
}

export function scoreMatch(title: string, query: string) {
    const t = title.toLowerCase();
    const q = query.toLowerCase();
    if (t === q) return 0;
    if (t.startsWith(q)) return 1;
    const idx = t.indexOf(q);
    if (idx >= 0) return 2 + idx / 100;
    const dist = levenshtein(t, q);
    const norm = dist / Math.max(t.length, q.length, 1);
    return 5 + norm;
}

export async function fetchAllNodes(state: WorkspaceState) {
    if (state.allNodesCache) return state.allNodesCache;
    const baseUrl = state.mode === 'public'
        ? '/api/v1/workspace/public-nodes'
        : state.mode === 'shared'
        ? '/api/v1/workspace/shared-nodes'
        : '/api/v1/workspace/nodes';
    const collected: any[] = [];
    const queue: string[] = ['root'];
    while (queue.length) {
        const parentId = queue.shift() as string;
        const response = await api.get(`${baseUrl}?parent_id=${parentId}`);
        const nodes = (response?.nodes || []) as any[];
        collected.push(...nodes);
        nodes.forEach((node) => {
            if (node.node_type === 'folder') {
                queue.push(node.id);
            }
        });
    }
    state.allNodesCache = collected;
    return collected;
}

export async function runSearch(state: WorkspaceState, raw: string, renderItems: (nodes: any[]) => void, refreshNodes: (parentId: string) => Promise<void>) {
    console.log('[runSearch] Starting search with query:', raw);
    const parsed = parseSearch(raw);
    console.log('[runSearch] Parsed:', parsed);
    if (!parsed) {
        console.log('[runSearch] No parsed query, refreshing current folder');
        await refreshNodes(state.currentParentId);
        return;
    }
    if (!parsed.query) {
        console.log('[runSearch] Empty query, refreshing current folder');
        await refreshNodes(state.currentParentId);
        return;
    }
    console.log('[runSearch] Fetching all nodes...');
    const nodes = await fetchAllNodes(state);
    console.log('[runSearch] Found', nodes.length, 'total nodes');
    const filtered = nodes.filter((node) => {
        if (parsed.type && node.node_type !== parsed.type) return false;
        return true;
    });
    console.log('[runSearch] Filtered to', filtered.length, 'nodes');
    const ranked = filtered
        .map((node) => ({
            node,
            score: scoreMatch(node.title || '', parsed.query),
        }))
        .sort((a, b) => a.score - b.score)
        .map((entry) => entry.node);
    console.log('[runSearch] Ranked', ranked.length, 'results, rendering...');

    // Temporarily disable sorting to preserve relevance ranking
    const originalSortKey = state.sortKey;
    console.log('[runSearch] Temporarily setting sortKey to null to preserve ranking');
    state.sortKey = null;
    renderItems(ranked);
    state.sortKey = originalSortKey;
    console.log('[runSearch] Restored sortKey to:', originalSortKey);

    console.log('[runSearch] ✓ Search complete');
}
