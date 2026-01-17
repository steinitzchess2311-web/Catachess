import { api } from '../../../assets/api';
import { Chessboard } from '../../chessboard';
import { initDiscussion } from '../../discussion/events';
import { fenToBoardPosition } from '../../chessboard/utils/api';

export async function initStudy(container: HTMLElement, studyId: string) {
    // 1. Load Template
    const template = document.getElementById('study-template') as HTMLTemplateElement;
    if (!template) return;
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    // 2. Select Elements
    const boardMount = container.querySelector('#board-mount') as HTMLElement;
    const chapterList = container.querySelector('#chapter-list') as HTMLElement;
    const moveTree = container.querySelector('#move-tree') as HTMLElement;
    const discussionMount = container.querySelector('#discussion-mount') as HTMLElement;
    const tabBtns = container.querySelectorAll('.tab-btn');
    const tabContents = container.querySelectorAll('.tab-content');

    // 3. State
    let currentStudy: any = null;
    let currentChapter: any = null;
    let board: Chessboard | null = null;
    let discussion: any = null;
    let currentPgn: string | null = null;

    // 4. Initialization
    let heartbeatInterval: any = null;

    const startHeartbeat = () => {
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        heartbeatInterval = setInterval(sendHeartbeat, 30000);
        sendHeartbeat(); // Initial call
    };

    const sendHeartbeat = async () => {
        if (!currentChapter) return;
        try {
            await api.post('/api/v1/workspace/presence/heartbeat', {
                study_id: studyId,
                chapter_id: currentChapter.id,
                move_path: null // TODO: Get current move path from board
            });
        } catch (error) {
            console.error('Heartbeat failed:', error);
        }
    };

    const loadStudyData = async () => {
        try {
            const response = await api.get(`/api/v1/workspace/studies/${studyId}`);
            currentStudy = response.study;
            renderChapters(response.chapters);
            
            if (response.chapters.length > 0) {
                selectChapter(response.chapters[0]);
                startHeartbeat();
            }
        } catch (error) {
            console.error('Failed to load study:', error);
        }
    };

    const loadChapterPgn = async (chapterId: string) => {
        try {
            const response = await api.post(`/api/v1/workspace/studies/${studyId}/pgn/export/raw`, {
                chapter_id: chapterId,
                for_clipboard: true,
            });
            currentPgn = response.pgn_text || '';
            renderMoveTree(currentPgn);
        } catch (error) {
            console.error('Failed to load PGN:', error);
            currentPgn = null;
            moveTree.innerHTML = '<div class="move-tree-empty">PGN unavailable</div>';
        }
    };

    const parsePgnMoves = (pgnText: string) => {
        const lines = pgnText
            .split('\n')
            .filter((line) => line.trim() && !line.startsWith('['));
        const movetext = lines.join(' ').trim();
        if (!movetext) return [];

        const tokens = movetext.split(/\s+/);
        const moves: Array<{ ply: number; moveNumber: number; color: 'w' | 'b'; san: string }> = [];
        let ply = 0;

        for (const token of tokens) {
            if (!token) continue;
            if (/^\d+\.+$/.test(token) || /^\d+\.\.\.$/.test(token)) {
                continue;
            }
            if (/^(1-0|0-1|1\/2-1\/2|\*)$/.test(token)) {
                break;
            }
            if (token.startsWith('{') || token.startsWith('(')) {
                continue;
            }
            ply += 1;
            const moveNumber = Math.floor((ply + 1) / 2);
            const color: 'w' | 'b' = ply % 2 === 1 ? 'w' : 'b';
            moves.push({ ply, moveNumber, color, san: token });
        }
        return moves;
    };

    const renderMoveTree = (pgnText: string) => {
        moveTree.innerHTML = '';
        const moves = parsePgnMoves(pgnText);

        if (!moves.length) {
            moveTree.innerHTML = '<div class="move-tree-empty">No moves yet</div>';
            return;
        }

        moves.forEach((move) => {
            const btn = document.createElement('button');
            btn.className = 'move-tree-item';
            btn.type = 'button';
            btn.textContent = `${move.moveNumber}${move.color === 'b' ? '...' : '.'} ${move.san}`;
            btn.addEventListener('click', async () => {
                if (!currentPgn || !board) return;
                try {
                    const result = await api.post('/api/games/pgn/fen', {
                        pgn: currentPgn,
                        ply: move.ply,
                    });
                    const position = fenToBoardPosition(result.fen);
                    board.setPosition(position);
                } catch (error) {
                    console.error('Failed to resolve FEN:', error);
                }
            });
            moveTree.appendChild(btn);
        });
    };

    const renderChapters = (chapters: any[]) => {
        chapterList.innerHTML = '';
        const tpl = document.getElementById('chapter-item-template') as HTMLTemplateElement;
        
        chapters.forEach(ch => {
            const item = document.importNode(tpl.content, true);
            const div = item.querySelector('.chapter-item') as HTMLElement;
            div.querySelector('.chapter-order')!.textContent = ch.order.toString();
            div.querySelector('.chapter-title')!.textContent = ch.title;
            
            div.addEventListener('click', () => selectChapter(ch));
            chapterList.appendChild(item);
        });
    };

    const selectChapter = (ch: any) => {
        currentChapter = ch;
        // Update UI
        container.querySelectorAll('.chapter-item').forEach(el => {
            el.classList.toggle('active', (el as HTMLElement).dataset.id === ch.id);
        });

        // Initialize/Update Board
        if (!board) {
            board = new Chessboard(boardMount, {
                gameId: ch.id,
                onMove: (move) => handleMove(move)
            });
        } else {
            // Update board position if needed
            // board.loadPGN(ch.pgn); // Assuming board has this
        }

        loadChapterPgn(ch.id);

        // Initialize Discussion
        if (!discussion) {
            discussion = initDiscussion(discussionMount, {
                targetType: 'chapter',
                targetId: ch.id
            });
        } else {
            discussion.updateContext('chapter', ch.id);
        }
    };

    const handleMove = async (move: any) => {
        try {
            // POST /api/v1/workspace/studies/{id}/chapters/{id}/moves
            await api.post(`/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/moves`, {
                parent_id: move.parentId,
                san: move.san,
                uci: move.uci,
                fen: move.fen,
                move_number: move.number,
                color: move.color
            });
        } catch (error) {
            console.error('Failed to save move:', error);
        }
    };

    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = (btn as HTMLElement).dataset.tab;
            tabBtns.forEach(b => b.classList.toggle('active', b === btn));
            tabContents.forEach(c => {
                c.classList.toggle('active', c.id === `tab-${tab}`);
            });
        });
    });

    // Start
    loadStudyData();
}
