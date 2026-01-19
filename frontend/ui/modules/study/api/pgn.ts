import { api } from '../../../assets/api';

type PGNDetectGame = {
    index: number;
    headers: Record<string, string>;
    movetext: string;
};

type PGNDetectResponse = {
    game_count: number;
    games: PGNDetectGame[];
};

export async function detectPGN(pgnText: string): Promise<PGNDetectResponse> {
    try {
        return await api.post('/api/games/pgn/detect', { pgn_text: pgnText });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to detect PGN';
        if (message.toLowerCase().includes('empty pgn')) {
            throw new Error('PGN file is empty.');
        }
        throw new Error(message || 'Failed to detect PGN.');
    }
}

// ============================================================================
// ShowDTO API (PGN v2)
// ============================================================================

export type ShowDTOHeader = {
    k: string;
    v: string;
};

export type ShowDTONode = {
    node_id: string;
    parent_id: string | null;
    san: string;
    uci: string;
    ply: number;
    move_number: number;
    fen: string;
    comment_before: string | null;
    comment_after: string | null;
    nags: number[];
    main_child: string | null;
    variations: string[];
};

export type ShowDTORenderToken =
    | { t: 'move'; node: string; label: string; san: string }
    | { t: 'comment'; node: string; text: string }
    | { t: 'variation_start'; from: string }
    | { t: 'variation_end' };

export type ShowDTOResponse = {
    headers: ShowDTOHeader[];
    nodes: Record<string, ShowDTONode>;
    render: ShowDTORenderToken[];
    root_fen: string | null;
    result: string | null;
};

/**
 * Feature flag for ShowDTO (v2) rendering.
 * Grey rollout default is disabled; localStorage can override.
 */
export const USE_SHOW_DTO = (() => {
    // Check for localStorage flag
    if (typeof window !== 'undefined') {
        const localFlag = localStorage.getItem('catachess_use_show_dto');
        if (localFlag !== null) {
            return localFlag === 'true';
        }
    }
    // Default: disabled for staged rollout
    return false;
})();

/**
 * Fetch ShowDTO for a chapter.
 *
 * @param studyId Study ID
 * @param chapterId Chapter ID
 * @returns ShowDTO response
 */
export async function fetchShowDTO(studyId: string, chapterId: string): Promise<ShowDTOResponse> {
    try {
        return await api.get(`/api/v1/workspace/studies/${studyId}/chapters/${chapterId}/show`);
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch ShowDTO';
        throw new Error(message);
    }
}

/**
 * Fetch FEN for a specific node.
 *
 * @param studyId Study ID
 * @param chapterId Chapter ID
 * @param nodeId Node ID
 * @returns Node FEN data
 */
export async function fetchNodeFen(studyId: string, chapterId: string, nodeId: string): Promise<{
    fen: string;
    node_id: string;
    san: string;
    uci: string;
    move_number: number;
    color: string;
}> {
    try {
        return await api.get(`/api/v1/workspace/studies/${studyId}/chapters/${chapterId}/fen/${nodeId}`);
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch node FEN';
        throw new Error(message);
    }
}

/**
 * Toggle ShowDTO feature flag.
 * Call this to switch between legacy and v2 rendering.
 */
export function toggleShowDTO(): boolean {
    const current = localStorage.getItem('catachess_use_show_dto') === 'true';
    const next = !current;
    localStorage.setItem('catachess_use_show_dto', String(next));
    console.log(`ShowDTO ${next ? 'enabled' : 'disabled'}. Refresh to apply.`);
    return next;
}

/**
 * Check if ShowDTO is enabled.
 */
export function isShowDTOEnabled(): boolean {
    const localFlag = localStorage.getItem('catachess_use_show_dto');
    if (localFlag === null) {
        return USE_SHOW_DTO;
    }
    return localFlag === 'true';
}
