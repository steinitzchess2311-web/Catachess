from typing import Optional

from core.chess_basic.pgn.common.pgn_types import NAG_SYMBOLS
from modules.workspace.pgn.serializer.to_pgn import tree_to_pgn
from modules.workspace.pgn.serializer.to_tree import VariationNode


class PgnGameTree:
    def __init__(self, start_fen: str, headers: dict[str, str]) -> None:
        self.start_fen = start_fen
        self.headers = headers
        self.root: Optional[VariationNode] = None
        self._fen_index: dict[str, VariationNode] = {}
        self._id_index: dict[str, VariationNode] = {}

    def set_tag(self, key: str, value: str) -> None:
        self.headers[key] = value

    def add_move(
        self,
        *,
        position_fen: str,
        new_fen: str,
        move_uci: str,
        san: str,
        move_number: int,
        color: str,
        move_id: Optional[str],
        parent_move_id: Optional[str],
        comment: Optional[str],
        nag: Optional[int],
    ) -> VariationNode:
        parent = self._id_index.get(parent_move_id) if parent_move_id else None
        if not parent:
            if position_fen == self.start_fen:
                parent = self.root
            else:
                parent = self._fen_index.get(position_fen)

        nag_symbol = NAG_SYMBOLS.get(nag) if nag else None
        node = VariationNode(
            move_number=move_number,
            color=color,
            san=san,
            uci=move_uci,
            fen=new_fen,
            nag=nag_symbol,
            comment=comment,
        )

        if self.root is None:
            node.rank = 0
            self.root = node
            return self._register(node, move_id)

        if parent is None:
            parent = self.root

        existing = next((c for c in parent.children if c.uci == move_uci), None)
        if existing:
            if comment:
                existing.comment = comment
            if nag:
                existing.nag = nag_symbol
            return self._register(existing, move_id)

        if parent == self.root and position_fen == self.start_fen:
            node.rank = self._next_rank(parent)
        else:
            node.rank = 0 if not self._has_mainline(parent) else self._next_rank(parent)

        parent.children.append(node)
        return self._register(node, move_id)

    def to_pgn(self) -> str:
        return tree_to_pgn(self.root, self.headers, self.headers.get("Result"))

    def mainline_count(self) -> int:
        count = 0
        current = self.root
        while current:
            count += 1
            current = next((c for c in current.children if c.rank == 0), None)
        return count

    def _register(self, node: VariationNode, move_id: Optional[str]) -> VariationNode:
        self._fen_index[node.fen] = node
        if move_id:
            self._id_index[move_id] = node
        return node

    def _next_rank(self, parent: VariationNode) -> int:
        return max((c.rank for c in parent.children), default=0) + 1

    def _has_mainline(self, parent: VariationNode) -> bool:
        return any(child.rank == 0 for child in parent.children)
