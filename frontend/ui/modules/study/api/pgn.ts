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
