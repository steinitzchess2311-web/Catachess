import type { ShowDTONode, ShowDTORenderToken, ShowDTOResponse } from './api/pgn';

type LegacyMove = {
    id: string;
    moveNumber: number;
    color: 'white' | 'black';
    san: string;
    fen: string;
    annotationId: string | null;
    annotationText: string | null;
    annotationVersion: number | null;
};

type Handlers = {
    onSelect: (nodeId: string) => void;
    onHover: (nodeId: string | null, isHovering: boolean) => void;
};

export class PgnRenderer {
    private container: HTMLElement;
    private showWrapper: HTMLElement | null = null;
    private mainlineWrapper: HTMLElement | null = null;
    private nodeElements = new Map<string, HTMLElement>();

    constructor(container: HTMLElement) {
        this.container = container;
    }

    clear(): void {
        this.container.innerHTML = '';
        this.showWrapper = null;
        this.mainlineWrapper = null;
        this.nodeElements.clear();
    }

    renderLegacy(moves: LegacyMove[], onSelect: (moveId: string) => void): void {
        this.clear();
        if (!moves.length) {
            this.container.innerHTML = '<div class="move-tree-empty">No moves yet</div>';
            return;
        }
        const list = document.createElement('div');
        list.className = 'pgn-legacy-list';
        moves.forEach((move) => {
            const moveEl = document.createElement('button');
            moveEl.className = 'move-token';
            moveEl.type = 'button';
            moveEl.dataset.moveId = move.id;
            const label = move.color === 'white' ? `${move.moveNumber}.` : `${move.moveNumber}...`;
            moveEl.innerHTML = `<span class="move-label">${label}</span><span class="move-san">${move.san}</span>`;
            moveEl.addEventListener('click', () => onSelect(move.id));
            list.appendChild(moveEl);
            list.appendChild(document.createTextNode(' '));
        });
        this.container.appendChild(list);
    }

    renderShow(showDTO: ShowDTOResponse, handlers: Handlers): void {
        this.clear();
        this.showWrapper = document.createElement('div');
        this.showWrapper.className = 'pgn-output-wrapper';
        this.container.appendChild(this.showWrapper);

        const headerInfo = document.createElement('div');
        headerInfo.className = 'pgn-header-info';
        const rootFenSpan = document.createElement('span');
        rootFenSpan.textContent = `Start FEN: ${showDTO.root_fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'}`;
        headerInfo.appendChild(rootFenSpan);
        this.showWrapper.appendChild(headerInfo);

        const tokens = showDTO.render || [];
        if (!tokens.length) {
            const empty = document.createElement('div');
            empty.className = 'move-tree-empty';
            empty.textContent = 'No moves yet';
            this.showWrapper.appendChild(empty);
            return;
        }

        this.renderTokensInChunks(tokens, handlers, showDTO.result || null);
    }

    appendMainline(node: ShowDTONode, label: string, handlers: Handlers): boolean {
        if (!this.showWrapper) return false;
        if (!this.mainlineWrapper) {
            this.mainlineWrapper = document.createElement('div');
            this.mainlineWrapper.className = 'pgn-mainline-wrapper';
            this.showWrapper.appendChild(this.mainlineWrapper);
        }
        const moveEl = this.createMoveElement(node.node_id, label, node.san, handlers);
        this.mainlineWrapper.appendChild(moveEl);
        this.mainlineWrapper.appendChild(document.createTextNode(' '));
        return true;
    }

    private renderTokensInChunks(tokens: ShowDTORenderToken[], handlers: Handlers, result: string | null): void {
        if (!this.showWrapper) return;
        const stack: HTMLElement[] = [this.showWrapper];
        let variationLevel = 0;
        let index = 0;
        const chunkSize = 75;

        const renderChunk = () => {
            const end = Math.min(index + chunkSize, tokens.length);
            while (index < end) {
                const token = tokens[index];
                this.appendToken(token, stack, handlers, () => variationLevel += 1, () => variationLevel -= 1, () => variationLevel);
                index += 1;
            }
            if (index < tokens.length) {
                requestAnimationFrame(renderChunk);
                return;
            }
            if (result) {
                const resultSpan = document.createElement('span');
                resultSpan.className = 'pgn-result';
                resultSpan.textContent = ` ${result}`;
                this.showWrapper?.appendChild(resultSpan);
            }
        };

        requestAnimationFrame(renderChunk);
    }

    private appendToken(
        token: ShowDTORenderToken,
        stack: HTMLElement[],
        handlers: Handlers,
        incVariation: () => void,
        decVariation: () => void,
        getVariation: () => number,
    ): void {
        const parent = stack[stack.length - 1];
        if (token.t === 'move') {
            const el = this.createMoveElement(token.node, token.label, token.san, handlers);
            parent.appendChild(el);
            parent.appendChild(document.createTextNode(' '));
            return;
        }
        if (token.t === 'comment') {
            const commentEl = this.createCommentElement(token.node, token.text);
            parent.appendChild(commentEl);
            parent.appendChild(document.createTextNode(' '));
            return;
        }
        if (token.t === 'variation_start') {
            incVariation();
            const level = Math.min(getVariation(), 5);
            const container = document.createElement('span');
            container.className = `variation-container variation-level-${level}`;
            container.style.marginLeft = `${level * 10}px`;
            parent.appendChild(container);
            stack.push(container);
            return;
        }
        if (token.t === 'variation_end') {
            stack.pop();
            const outer = stack[stack.length - 1] || parent;
            const closeParen = document.createElement('span');
            closeParen.className = 'variation-paren variation-end-paren';
            closeParen.textContent = ')';
            outer.appendChild(closeParen);
            outer.appendChild(document.createTextNode(' '));
            decVariation();
        }
    }

    private createMoveElement(nodeId: string, label: string, san: string, handlers: Handlers): HTMLElement {
        const moveEl = document.createElement('button');
        moveEl.className = 'move-token';
        moveEl.type = 'button';
        moveEl.dataset.nodeId = nodeId;
        moveEl.innerHTML = `<span class="move-label">${label}</span><span class="move-san">${san}</span>`;
        moveEl.addEventListener('click', () => handlers.onSelect(nodeId));
        moveEl.addEventListener('mouseenter', () => handlers.onHover(nodeId, true));
        moveEl.addEventListener('mouseleave', () => handlers.onHover(nodeId, false));
        this.nodeElements.set(nodeId, moveEl);
        return moveEl;
    }

    private createCommentElement(nodeId: string, text: string): HTMLElement {
        const commentWrapper = document.createElement('span');
        commentWrapper.className = 'comment-wrapper';
        commentWrapper.dataset.nodeId = nodeId;
        const commentTextSpan = document.createElement('span');
        commentTextSpan.className = 'comment-text';
        commentTextSpan.textContent = text;
        commentWrapper.appendChild(commentTextSpan);
        return commentWrapper;
    }
}
