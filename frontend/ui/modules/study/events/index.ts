import { ChessboardV2 } from '../../chessboard_v2';
import { createEngineAnalysis, createImitatorPanel } from '../../chessboard';
import { initDiscussion } from '../../discussion/events';
import { fenToBoardPosition } from '../../chessboard/utils/api';
import { detectPGN } from '../api/pgn';
import { api } from '../../../assets/api';

export async function initStudy(container: HTMLElement, studyId: string): Promise<ChessboardV2> {
    // 1. Load Template
    const template = document.getElementById('study-template') as HTMLTemplateElement;
    if (!template) throw new Error('Study template not found');
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    // 2. Select Elements
    const boardMount = container.querySelector('#board-mount') as HTMLElement;
    const chapterList = container.querySelector('#chapter-list') as HTMLElement;
    const moveTree = container.querySelector('#move-tree') as HTMLElement;
    const discussionMount = container.querySelector('#discussion-mount') as HTMLElement;
    const addChapterBtn = container.querySelector('#add-chapter-btn') as HTMLButtonElement;
    const importPgnBtn = container.querySelector('#import-pgn-btn') as HTMLButtonElement;
    const backBtn = container.querySelector('#back-btn') as HTMLButtonElement;
    const pgnCommentInput = container.querySelector('#pgn-comment-input') as HTMLTextAreaElement;
    const pgnCommentBtn = container.querySelector('#pgn-comment-btn') as HTMLButtonElement;
    const firstMoveBtn = container.querySelector('#first-move') as HTMLButtonElement;
    const prevMoveBtn = container.querySelector('#prev-move') as HTMLButtonElement;
    const nextMoveBtn = container.querySelector('#next-move') as HTMLButtonElement;
    const lastMoveBtn = container.querySelector('#last-move') as HTMLButtonElement;
    const flipBtn = container.querySelector('#flip-board') as HTMLButtonElement;
    const tabBtns = container.querySelectorAll('.tab-btn');
    const tabContents = container.querySelectorAll('.tab-content');
    const engineMount = container.querySelector('#engine-mount') as HTMLElement;
    const imitatorMount = container.querySelector('#imitator-mount') as HTMLElement;
    const studyContainer = container.querySelector('.study-container') as HTMLElement;
    const leftSplitter = container.querySelector('[data-split="left"]') as HTMLElement;
    const rightSplitter = container.querySelector('[data-split="right"]') as HTMLElement;

    // 3. State
    let currentStudy: any = null;
    let currentChapter: any = null;
    let board: ChessboardV2 | null = null;
    let discussion: any = null;
    let currentPgn: string | null = null;
    let chapters: any[] = [];
    let lastMoveId: string | null = null;
    let currentMoves: Array<{
        id: string;
        moveNumber: number;
        color: 'white' | 'black';
        san: string;
        fen: string;
        annotationId: string | null;
        annotationText: string | null;
        annotationVersion: number | null;
    }> = [];
    let selectedMoveId: string | null = null;
    let selectedAnnotationId: string | null = null;
    let selectedAnnotationVersion: number | null = null;
    let currentPly = 0;
    let engineAnalysis: any = null;
    let imitatorPanel: any = null;

    // 4. Initialization
    let heartbeatInterval: any = null;

    const setupSplitters = () => {
        if (!studyContainer || !leftSplitter || !rightSplitter) return;
        const splitterWidth = 8;
        const minLeft = 180;
        const minRight = 240;
        const minCenter = 360;

        const applySizes = (left: number, right: number) => {
            studyContainer.style.setProperty('--study-left-width', `${left}px`);
            studyContainer.style.setProperty('--study-right-width', `${right}px`);
        };

        const getSizes = () => {
            const styles = getComputedStyle(studyContainer);
            const left = parseFloat(styles.getPropertyValue('--study-left-width')) ||
                (container.querySelector('.study-left-panel') as HTMLElement).offsetWidth;
            const right = parseFloat(styles.getPropertyValue('--study-right-width')) ||
                (container.querySelector('.study-right-panel') as HTMLElement).offsetWidth;
            const total = studyContainer.getBoundingClientRect().width;
            return { left, right, total };
        };

        const clamp = (value: number, min: number, max: number) => {
            return Math.max(min, Math.min(max, value));
        };

        const startDrag = (side: 'left' | 'right', event: PointerEvent) => {
            const { left, right, total } = getSizes();
            const startX = event.clientX;
            const maxLeft = total - minRight - minCenter - splitterWidth * 2;
            const maxRight = total - minLeft - minCenter - splitterWidth * 2;

            const onMove = (moveEvent: PointerEvent) => {
                const delta = moveEvent.clientX - startX;
                if (side === 'left') {
                    const nextLeft = clamp(left + delta, minLeft, maxLeft);
                    applySizes(nextLeft, right);
                    return;
                }
                const nextRight = clamp(right - delta, minRight, maxRight);
                applySizes(left, nextRight);
            };

            const onStop = () => {
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onStop);
                document.body.style.cursor = '';
            };

            document.body.style.cursor = 'col-resize';
            window.addEventListener('pointermove', onMove);
            window.addEventListener('pointerup', onStop);
        };

        leftSplitter.addEventListener('pointerdown', (event) => startDrag('left', event));
        rightSplitter.addEventListener('pointerdown', (event) => startDrag('right', event));
    };

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
            chapters = response.chapters || [];
            renderChapters(chapters);
            
                        if (chapters.length > 0) {
            
                            await selectChapter(chapters[0]); // Await selectChapter
            
                            startHeartbeat();
            
                        } else {
            
                            renderEmptyState();
            
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
            
                        await loadMainlineMoves();
            
                        currentPly = 0;
            
                        await updateBoardForPly(currentPly);
            
                    } catch (error) {
            
                        console.error('Failed to load PGN:', error);
            
                        currentPgn = null;
            
                        currentMoves = [];
            
                        moveTree.innerHTML = '<div class="move-tree-empty">PGN unavailable</div>';
            
                    }
            
                };
            
            
            
                const loadMainlineMoves = async (moveIdToSelect?: string) => {
            
                    if (!currentChapter) return;
            
                    try {
            
                        const response = await api.get(
            
                            `/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/moves/mainline`
            
                        );
            
                        currentMoves = (response?.moves || []).map((move: any) => ({
            
                            id: move.id,
            
                            moveNumber: move.move_number,
            
                            color: move.color,
            
                            san: move.san,
            
                            fen: move.fen,
            
                            annotationId: move.annotation_id,
            
                            annotationText: move.annotation_text,
            
                            annotationVersion: move.annotation_version,
            
                        }));
            
                        renderMoveTree();
            
                        if (moveIdToSelect) {
            
                            const index = currentMoves.findIndex((item) => item.id === moveIdToSelect);
            
                            if (index >= 0) {
            
                                selectMove(currentMoves[index], index);
            
                            }
            
                        }
            
                    } catch (error) {
            
                        console.error('Failed to load move list:', error);
            
                        currentMoves = [];
            
                        renderMoveTree();
            
                    }
            
                };
            
            
            
                const selectMove = (move: typeof currentMoves[number], index: number) => {
            
                    if (!board) return;
            
                    selectedMoveId = move.id;
            
                    selectedAnnotationId = move.annotationId;
            
                    selectedAnnotationVersion = move.annotationVersion;
            
                    pgnCommentInput.value = ''; // This line is changed in replace
            
                    currentPly = index + 1;
            
                    board.setPosition(fenToBoardPosition(move.fen));
            
                    updateAnalysisPanels();
            
                };
            
            
            
                const renderMoveTree = () => {
            
                    moveTree.innerHTML = '';
            
                    if (!currentMoves.length) {
            
                        moveTree.innerHTML = '<div class="move-tree-empty">No moves yet</div>';
            
                        return;
            
                    }
            
            
            
                    const rows = new Map<number, { white?: typeof currentMoves[number]; black?: typeof currentMoves[number] }>();
            
                    currentMoves.forEach((move) => {
            
                        const row = rows.get(move.moveNumber) || {};
            
                        if (move.color === 'white') {
            
                            row.white = move;
            
                        } else {
            
                            row.black = move;
            
                        }
            
                        rows.set(move.moveNumber, row);
            
                    });
            
            
            
                    const orderedNumbers = Array.from(rows.keys()).sort((a, b) => a - b);
            
                    orderedNumbers.forEach((moveNumber) => {
            
                        const row = rows.get(moveNumber);
            
                        const rowEl = document.createElement('div');
            
                        rowEl.className = 'move-tree-row';
            
            
            
                        const numberEl = document.createElement('div');
            
                        numberEl.className = 'move-tree-number';
            
                        numberEl.textContent = `${moveNumber}.`;
            
                        rowEl.appendChild(numberEl);
            
            
            
                        const renderMoveButton = (move?: typeof currentMoves[number]) => {
            
                            const btn = document.createElement('button');
            
                            btn.className = 'move-tree-move';
            
                            btn.type = 'button';
            
                            btn.textContent = move ? move.san : '';
            
                            btn.disabled = !move;
            
                            if (move) {
            
                                btn.addEventListener('click', () => {
            
                                    const index = currentMoves.findIndex((item) => item.id === move.id);
            
                                    if (index >= 0) {
            
                                        selectMove(move, index);
            
                                    }
            
                                });
            
                            }
            
                            return btn;
            
                        };
            
            
            
                        rowEl.appendChild(renderMoveButton(row?.white));
            
                        rowEl.appendChild(renderMoveButton(row?.black));
            
                        moveTree.appendChild(rowEl);
            
                    });
            
                };
            
            
            
                const renderChapters = (chapters: any[]) => {
            
                    chapterList.innerHTML = '';
            
                    const tpl = document.getElementById('chapter-item-template') as HTMLTemplateElement;
            
                    
            
                    chapters.forEach(ch => {
            
                        const item = document.importNode(tpl.content, true);
            
                        const div = item.querySelector('.chapter-item') as HTMLElement;
            
                        div.dataset.id = ch.id;
            
                        div.querySelector('.chapter-order')!.textContent = ch.order.toString();
            
                        div.querySelector('.chapter-title')!.textContent = ch.title;
            
                        
            
                        div.addEventListener('click', () => selectChapter(ch));
            
                        chapterList.appendChild(item);
            
                    });
            
                };
            
            
            
                const renderEmptyState = () => {
            
                    chapterList.innerHTML = '<div class="chapter-empty">No chapters yet. Click + to add one.</div>';
            
                    moveTree.innerHTML = '<div class="move-tree-empty">No chapter selected</div>';
            
                    boardMount.innerHTML = '<div class="board-empty">Create a chapter to start</div>';
            
                    discussionMount.innerHTML = '<div class="discussion-empty">Select a chapter to view discussions.</div>';
            
                };
            
            
            
                const updateAnalysisPanels = () => {
            
                    if (!board) return;
            
                    const position = board.getPosition();
            
                    if (engineAnalysis) {
            
                        engineAnalysis.setPosition(position);
            
                        engineAnalysis.setMultipv(5);
            
                        engineAnalysis.analyze();
            
                    }
            
                    if (imitatorPanel) {
            
                        imitatorPanel.setPosition(position);
            
                    }
            
                };
            
            
            
                const selectChapter = async (ch: any) => { // Made async
            
                    currentChapter = ch;
            
                    selectedMoveId = null;
            
                    selectedAnnotationId = null;
            
                    selectedAnnotationVersion = null;
            
                    pgnCommentInput.value = '';
            
                    // Update UI
            
                    container.querySelectorAll('.chapter-item').forEach(el => {
            
                        el.classList.toggle('active', (el as HTMLElement).dataset.id === ch.id);
            
                    });
            
            
            
                    // Initialize/Update Board
            
                    if (!board) {
            
                        board = new ChessboardV2(boardMount, {
            
                            gameId: ch.id,
            
                            onMove: (move) => handleMove(move)
            
                        });
            
                        engineAnalysis = createEngineAnalysis(engineMount);
            
                        imitatorPanel = createImitatorPanel(imitatorMount);
            
                    } else {
            
                        // Update board position if needed
            
                        // board.loadPGN(ch.pgn); // Assuming board has this
            
                    }
            
            
            
                    await loadChapterPgn(ch.id); // Await this call
            
            
            
                    // Initialize Discussion (use study node for permissions)
            
                    if (!discussion) {
            
                        discussion = initDiscussion(discussionMount, {
            
                            targetType: 'study',
            
                            targetId: studyId
            
                        });
            
                    }
            
                    else {
            
                        discussion.updateContext('study', studyId);
            
                    }
            
                };
            
            
            
                const handleMove = async (move: any) => {
            
                    try {
            
                        if (!move?.san || !move?.uci || !move?.fen || !move?.number || !move?.color) {
            
                            console.error('Move metadata missing, skipping save:', move);
            
                            return;
            
                        }
            
                        // POST /api/v1/workspace/studies/{id}/chapters/{id}/moves
            
                        const response = await api.post(`/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/moves`, {
            
                            parent_id: move.parentId,
            
                            san: move.san,
            
                            uci: move.uci,
            
                            fen: move.fen,
            
                            move_number: move.number,
            
                            color: move.color
            
                        });
            
                        if (response?.id) {
            
                            lastMoveId = response.id;
            
                            selectedMoveId = response.id;
            
                            selectedAnnotationId = null;
            
                            selectedAnnotationVersion = null;
            
                            pgnCommentInput.value = '';
            
                        }
            
                        await loadMainlineMoves(response?.id);
            
                        updateAnalysisPanels();
            
                    } catch (error) {
            
                        console.error('Failed to save move:', error);
            
                    }
            
                };
            
            
            
                const addPgnComment = async () => {
            
                    const text = pgnCommentInput.value.trim();
            
                    if (!text) return;
            
                    const targetMoveId = selectedMoveId || lastMoveId;
            
                    if (!currentChapter || !targetMoveId) {
            
                        alert('Select a move first, then add a comment.');
            
                        return;
            
                    }
            
                    try {
            
                        if (selectedAnnotationId && selectedAnnotationVersion !== null) {
            
                            const updated = await api.put(
            
                                `/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/annotations/${selectedAnnotationId}`,
            
                                { text, version: selectedAnnotationVersion }
            
                            );
            
                            selectedAnnotationVersion = updated?.version ?? selectedAnnotationVersion;
            
                        } else if (selectedAnnotationId) {
            
                            const updated = await api.put(
            
                                `/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/annotations/${selectedAnnotationId}`,
            
                                { text, version: 1 }
            
                            );
            
                            selectedAnnotationVersion = updated?.version ?? selectedAnnotationVersion;
            
                        } else {
            
                            const created = await api.post(
            
                                `/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/moves/${targetMoveId}/annotations`,
            
                                { text }
            
                            );
            
                            selectedAnnotationId = created?.id || selectedAnnotationId;
            
                            selectedAnnotationVersion = created?.version ?? selectedAnnotationVersion;
            
                        }
            
                        await loadMainlineMoves(targetMoveId);
            
                    } catch (error) {
            
                        console.error('Failed to add PGN comment:', error);
            
                        alert('Failed to add PGN comment');
            
                    }
            
                };
            
            
            
                const updateBoardForPly = async (ply: number) => {
            
                    if (!board) return;
            
                    const maxPly = currentMoves.length;
            
                    const safePly = Math.max(0, Math.min(ply, maxPly));
            
                    if (safePly === 0) {
            
                        board.reset();
            
                        updateAnalysisPanels();
            
                        return;
            
                    }
            
                    const move = currentMoves[safePly - 1];
            
                    if (!move) return;
            
                    board.setPosition(fenToBoardPosition(move.fen));
            
                    updateAnalysisPanels();
            
                };
            
            
            
                const createChapter = async () => {
            
                    const title = window.prompt('Chapter title');
            
                    if (!title) return;
            
                    try {
            
                        const response = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, {
            
                            title,
            
                        });
            
                        chapters = [...chapters, response].sort((a, b) => a.order - b.order);
            
                        renderChapters(chapters);
            
                        await selectChapter(response); // Await selectChapter
            
                        startHeartbeat();
            
                    } catch (error) {
            
                        console.error('Failed to create chapter:', error);
            
                        alert('Failed to create chapter');
            
                    }
            
                };
            
            
            
                const importPgn = async () => {
            
                    const input = document.createElement('input');
            
                    input.type = 'file';
            
                    input.accept = '.pgn';
            
                    input.addEventListener('change', async () => {
            
                        const file = input.files?.[0];
            
                        if (!file) return;
            
                        try {
            
                            const pgnContent = await file.text();
            
                            const detection = await detectPGN(pgnContent);
            
                            if (!detection.game_count) {
            
                                alert('No games detected. Make sure the PGN has headers like [Event "..."].');
            
                                return;
            
                            }
            
            
            
                            const previewLines = detection.games.slice(0, 3).map((game) => {
            
                                const headers = game.headers || {};
            
                                const event = headers.Event || 'Unknown event';
            
                                const white = headers.White || '?';
            
                                const black = headers.Black || '?';
            
                                return `${game.index}. ${event} - ${white} vs ${black}`;
            
                            });
            
                            const preview = previewLines.length ? `\n${previewLines.join('\n')}` : '';
            
                            alert(`Detected ${detection.game_count} game(s).${preview}`);
            
            
            
                            if (detection.game_count > 64) {
            
                                const response = await api.post('/api/v1/workspace/studies/import-pgn', {
            
                                    pgn_content: pgnContent,
            
                                    base_title: currentStudy?.title || 'Imported PGN',
            
                                    parent_id: currentStudy?.parent_id || null,
            
                                    auto_split: true,
            
                                    visibility: currentStudy?.visibility || 'private',
            
                                });
            
                                if (response?.was_split) {
            
                                    const count = response.studies_created?.length || 0;
            
                                    alert(`PGN split into ${count} study(ies). Check workspace list.`);
            
                                    window.location.assign('/workspace-select');
            
                                    return;
            
                                }
            
                            } else {
            
                                await api.post(`/api/v1/workspace/studies/${studyId}/chapters/import-pgn`, {
            
                                    pgn_content: pgnContent,
            
                                });
            
                                await loadStudyData();
            
                            }
            
                        } catch (error) {
            
                            console.error('Failed to import PGN:', error);
            
                            const message = error instanceof Error ? error.message : 'Failed to import PGN';
            
                            alert(message);
            
                        }
            
                    });
            
                    input.click();
            
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
            
            
            
                if (!addChapterBtn) {
                    console.warn('Add chapter button not found.');
                }
                if (!importPgnBtn) {
                    console.warn('Import PGN button not found.');
                }

                addChapterBtn?.addEventListener('click', createChapter);

                importPgnBtn?.addEventListener('click', importPgn);

                studyContainer?.addEventListener('click', (event) => {
                    const target = event.target as HTMLElement | null;
                    if (!target) return;
                    const addBtn = target.closest('#add-chapter-btn');
                    if (addBtn) {
                        event.preventDefault();
                        event.stopPropagation();
                        createChapter();
                        return;
                    }
                    const importBtn = target.closest('#import-pgn-btn');
                    if (importBtn) {
                        event.preventDefault();
                        event.stopPropagation();
                        importPgn();
                    }
                });
            
                pgnCommentBtn?.addEventListener('click', addPgnComment);
            
                firstMoveBtn?.addEventListener('click', async () => {
            
                    currentPly = 0;
            
                    await updateBoardForPly(currentPly);
            
                });
            
                prevMoveBtn?.addEventListener('click', async () => {
            
                    currentPly = Math.max(0, currentPly - 1);
            
                    await updateBoardForPly(currentPly);
            
                });
            
                nextMoveBtn?.addEventListener('click', async () => {
            
                    currentPly = Math.min(currentMoves.length, currentPly + 1);
            
                    await updateBoardForPly(currentPly);
            
                });
            
                lastMoveBtn?.addEventListener('click', async () => {
            
                    currentPly = currentMoves.length;
            
                    await updateBoardForPly(currentPly);
            
                });
            
                flipBtn?.addEventListener('click', () => {
            
                    if (board) {
            
                        board.flip();
            
                    }
            
                });
            
                backBtn?.addEventListener('click', () => {
            
                    window.history.back();
            
                });
            
            
            
                // Start
            
                setupSplitters();
            
                await loadStudyData(); // Await this call
            
            
            
                if (!board) {
            
                  throw new Error("Chessboard failed to initialize.");
            
                }
            
                return board;
            
            }
