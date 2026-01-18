import { ChessboardV2 } from '../../chessboard_v2';
import { createEngineAnalysis, createImitatorPanel } from '../../chessboard';
import { initDiscussion } from '../../discussion/events';
import { fenToBoardPosition } from '../../chessboard/utils/api';
import {
    detectPGN,
    fetchShowDTO,
    isShowDTOEnabled,
    ShowDTOResponse,
    ShowDTONode,
    ShowDTORenderToken,
} from '../api/pgn';
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
    let currentShowDTO: ShowDTOResponse | null = null; // New state variable

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
                        let movesData: Array<{
                            id: string;
                            moveNumber: number;
                            color: 'white' | 'black';
                            san: string;
                            fen: string;
                            annotationId: string | null;
                            annotationText: string | null;
                            annotationVersion: number | null;
                        }> = [];

                        if (isShowDTOEnabled()) {
                            try {
                                const showResponse = await fetchShowDTO(studyId, currentChapter.id);
                                currentShowDTO = showResponse; // Store the full DTO
                                const nodes = showResponse.nodes;
                                let rootNodeId: string | null = null;

                                // Find the root node (ply 0, parent_id null, and has a main_child)
                                for (const nodeId in nodes) {
                                    const node = nodes[nodeId];
                                    if (node.ply === 0 && node.parent_id === null && node.main_child) {
                                        rootNodeId = node.node_id;
                                        break;
                                    }
                                }

                                // Populate movesData for backward compatibility (e.g., updateBoardForPly for non-ShowDTO parts)
                                // This still extracts mainline, but the rendering will use currentShowDTO.render
                                if (rootNodeId) {
                                    let currentShowNode = nodes[rootNodeId];
                                    while (currentShowNode && currentShowNode.main_child) {
                                        const nextNode = nodes[currentShowNode.main_child];
                                        if (nextNode) {
                                            movesData.push({
                                                id: nextNode.node_id,
                                                moveNumber: nextNode.move_number,
                                                color: nextNode.ply % 2 === 1 ? 'white' : 'black',
                                                san: nextNode.san,
                                                fen: nextNode.fen,
                                                annotationId: null,
                                                annotationText: nextNode.comment_after || nextNode.comment_before,
                                                annotationVersion: null,
                                            });
                                            currentShowNode = nextNode;
                                        } else {
                                            break;
                                        }
                                    }
                                } else {
                                    console.warn('Could not find a valid root node for ShowDTO.');
                                    currentShowDTO = null; // Mark as failed to load ShowDTO
                                }
                            } catch (showError) {
                                console.error('Failed to load moves using ShowDTO:', showError);
                                currentShowDTO = null; // Clear DTO on error
                            }
                        }

                        if (!currentShowDTO) { // If ShowDTO is not enabled or failed, use existing API
                             const response = await api.get(
                                `/api/v1/workspace/studies/${studyId}/chapters/${currentChapter.id}/moves/mainline`
                            );
                            movesData = (response?.moves || []).map((move: any) => ({
                                id: move.id,
                                moveNumber: move.move_number,
                                color: move.color,
                                san: move.san,
                                fen: move.fen,
                                annotationId: move.annotation_id,
                                annotationText: move.annotation_text,
                                annotationVersion: move.annotation_version,
                            }));
                        }

                        currentMoves = movesData;
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
            
            
            
                const selectMove = (nodeId: string) => {
                    if (!board || !currentShowDTO) return;

                    const node = currentShowDTO.nodes[nodeId];
                    if (!node) {
                        console.error('Node not found for ID:', nodeId);
                        return;
                    }
                    
                    selectedMoveId = nodeId;
                    // For now, we'll keep annotation IDs/versions as null if using ShowDTO
                    // This part needs more thought if editing annotations is desired with PGN v2
                    selectedAnnotationId = null; 
                    selectedAnnotationVersion = null;
                    pgnCommentInput.value = node.comment_after || node.comment_before || ''; 
                    
                    board.setPosition(fenToBoardPosition(node.fen));
                    updateAnalysisPanels();
                    // Update currentPly based on the selected node's ply
                    // This will need adjustment if we want to navigate through currentMoves for history
                    // For now, let's set it to the node's ply
                    currentPly = node.ply;

                    // Highlight selected move in the UI
                    moveTree.querySelectorAll('.move-token.active').forEach(el => el.classList.remove('active'));
                    const selectedMoveElement = moveTree.querySelector(`.move-token[data-node-id="${nodeId}"]`);
                    if (selectedMoveElement) {
                        selectedMoveElement.classList.add('active');
                    }
                };
                
                const hoverMove = (nodeId: string | null, isHovering: boolean) => {
                    if (!board || !currentShowDTO) return;
                    if (isHovering && nodeId) {
                        const node = currentShowDTO.nodes[nodeId];
                        if (node) {
                            board.setTemporaryPosition(fenToBoardPosition(node.fen));
                        }
                    } else {
                        // Revert to current selected move's FEN
                        if (selectedMoveId) {
                            const node = currentShowDTO.nodes[selectedMoveId];
                            if (node) {
                                board.setPosition(fenToBoardPosition(node.fen));
                            }
                        } else {
                            // If no move is selected, revert to the initial board position
                             board.reset(); // Assuming reset sets to initial FEN
                        }
                    }
                }

                const renderMoveTree = () => {
                    moveTree.innerHTML = '';
                    if (!currentShowDTO) {
                        moveTree.innerHTML = '<div class="move-tree-empty">PGN unavailable or ShowDTO failed to load.</div>';
                        return;
                    }

                    // New rendering logic using ShowDTO
                    const pgnOutputWrapper = document.createElement('div');
                    pgnOutputWrapper.className = 'pgn-output-wrapper';
                    moveTree.appendChild(pgnOutputWrapper);

                    // Display root_fen and result (initial status)
                    const headerInfo = document.createElement('div');
                    headerInfo.className = 'pgn-header-info';
                    const rootFenSpan = document.createElement('span');
                    rootFenSpan.textContent = `Start FEN: ${currentShowDTO.root_fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'}`;
                    headerInfo.appendChild(rootFenSpan);
                    pgnOutputWrapper.appendChild(headerInfo);

                    const currentContainerStack: HTMLElement[] = [pgnOutputWrapper];
                    let variationLevel = 0;

                    const createMoveElement = (nodeId: string, label: string, san: string): HTMLElement => {
                        const moveEl = document.createElement('button');
                        moveEl.className = 'move-token';
                        moveEl.type = 'button';
                        moveEl.dataset.nodeId = nodeId;
                        moveEl.innerHTML = `<span class="move-label">${label}</span><span class="move-san">${san}</span>`;
                        moveEl.addEventListener('click', () => selectMove(nodeId));
                        moveEl.addEventListener('mouseenter', () => hoverMove(nodeId, true));
                        moveEl.addEventListener('mouseleave', () => hoverMove(nodeId, false));
                        return moveEl;
                    };

                    const createCommentElement = (nodeId: string, text: string): HTMLElement => {
                        const commentWrapper = document.createElement('span');
                        commentWrapper.className = 'comment-wrapper';
                        commentWrapper.dataset.nodeId = nodeId;

                        // Use a more robust check for sentence end (Chinese specific)
                        const firstSentenceMatch = text.match(/^[^。！？.?!]+/);
                        let displayInitially = text;
                        let needsToggleButton = false;

                        if (firstSentenceMatch) {
                            const firstSentence = firstSentenceMatch[0];
                            if (firstSentence.length < text.length) {
                                displayInitially = firstSentence + '...';
                                needsToggleButton = true;
                            }
                        } else if (text.length > 120) {
                            displayInitially = text.substring(0, 120) + '...';
                            needsToggleButton = true;
                        }

                        const commentTextSpan = document.createElement('span');
                        commentTextSpan.className = 'comment-text';
                        commentTextSpan.textContent = displayInitially;
                        commentTextSpan.style.fontStyle = 'italic';
                        commentTextSpan.style.color = 'gray';
                        commentTextSpan.style.fontSize = '0.9em';
                        commentWrapper.appendChild(commentTextSpan);

                        if (needsToggleButton) {
                            const toggleButton = document.createElement('button');
                            toggleButton.className = 'comment-toggle';
                            toggleButton.textContent = '展开'; // "展开" for expand
                            toggleButton.style.background = 'none';
                            toggleButton.style.border = 'none';
                            toggleButton.style.color = 'blue';
                            toggleButton.style.cursor = 'pointer';
                            toggleButton.style.marginLeft = '5px';
                            commentWrapper.appendChild(toggleButton);

                            let expanded = false;
                            toggleButton.addEventListener('click', () => {
                                expanded = !expanded;
                                commentTextSpan.textContent = expanded ? text : displayInitially;
                                toggleButton.textContent = expanded ? '收起' : '展开'; // "收起" for collapse
                            });
                        }
                        return commentWrapper;
                    };


                    currentShowDTO.render.forEach(token => {
                        const currentParent = currentContainerStack[currentContainerStack.length - 1];
                        if (!currentParent) return;

                        if (token.t === 'move') {
                            const moveEl = createMoveElement(token.node, token.label, token.san);
                            currentParent.appendChild(moveEl);
                            currentParent.appendChild(document.createTextNode(' ')); // Add space between moves
                        } else if (token.t === 'comment') {
                            const commentEl = createCommentElement(token.node, token.text);
                            currentParent.appendChild(commentEl);
                            currentParent.appendChild(document.createTextNode(' '));
                        } else if (token.t === 'variation_start') {
                            variationLevel++;
                            // Frontend no longer adds '(', as it's expected to be in the first move's label from the backend ShowDTO
                            const cappedVariationLevel = Math.min(variationLevel, 5); // Cap nesting at 5 for visual consistency
                            if (variationLevel > 5) {
                                console.warn(`Variation nesting exceeded 5 levels. Capping visual indentation.`);
                            }
                            const variationContainer = document.createElement('span');
                            variationContainer.className = `variation-container variation-level-${cappedVariationLevel}`;
                            variationContainer.style.marginLeft = `${cappedVariationLevel * 10}px`; // Simple indent
                            currentParent.appendChild(variationContainer);
                            currentContainerStack.push(variationContainer);
                        } else if (token.t === 'variation_end') {
                            const popped = currentContainerStack.pop();
                            if (popped) {
                                const closeParen = document.createElement('span');
                                closeParen.className = 'variation-paren variation-end-paren';
                                closeParen.textContent = ')';
                                (currentContainerStack[currentContainerStack.length - 1] || pgnOutputWrapper).appendChild(closeParen);
                                (currentContainerStack[currentContainerStack.length - 1] || pgnOutputWrapper).appendChild(document.createTextNode(' '));
                            }
                            variationLevel--;
                        }
                    });

                    // Display result at the end
                    if (currentShowDTO.result) {
                        const resultSpan = document.createElement('span');
                        resultSpan.className = 'pgn-result';
                        resultSpan.textContent = ` ${currentShowDTO.result}`;
                        pgnOutputWrapper.appendChild(resultSpan);
                    }
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

                    if (currentShowDTO && currentShowDTO.root_fen) {
                        board.setPosition(fenToBoardPosition(currentShowDTO.root_fen));
                        currentPly = 0; // Set ply to 0 for initial position
                    } else {
                        currentPly = 0;
                        await updateBoardForPly(currentPly);
                    }
            
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
            
                    // If using ShowDTO, direct ply-based navigation through currentMoves is less straightforward.
                    // We need a way to map ply to a nodeId from the DTO.
                    // For now, if ShowDTO is enabled, we'll rely on selectMove with a specific nodeId,
                    // or enhance this to find a node by ply if needed.
                    if (currentShowDTO && currentShowDTO.nodes) {
                        const nodesByPly = Object.values(currentShowDTO.nodes).filter(node => node.ply === ply && node.san !== "<root>");
                        if (nodesByPly.length > 0) {
                            // Prioritize mainline node if available
                            const mainlineNode = nodesByPly.find(node => {
                                const parentNode = currentShowDTO?.nodes[node.parent_id || ''];
                                return parentNode && parentNode.main_child === node.node_id;
                            }) || nodesByPly[0]; // Fallback to first node at that ply
                            selectMove(mainlineNode.node_id);
                            return;
                        }
                    }

                    // Fallback to existing currentMoves logic if ShowDTO not used or node not found
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

