"""Build PGN variation trees directly from DB variations + annotations.

DEPRECATED: Use backend.core.real_pgn for new PGN processing.
"""

from collections import defaultdict
from typing import Iterable

from modules.workspace.db.tables.variations import MoveAnnotation, Variation
from modules.workspace.pgn.serializer.to_tree import VariationNode


def variations_to_tree(
    variations: Iterable[Variation],
    annotations: Iterable[MoveAnnotation],
) -> VariationNode | None:
    """Convert DB variations into a VariationNode tree."""
    variations = list(variations)
    if not variations:
        return None

    annotation_map = {ann.move_id: ann for ann in annotations}
    nodes: dict[str, VariationNode] = {}
    children: dict[str | None, list[Variation]] = defaultdict(list)

    # Build nodes and index by parent_id for fast child lookup.
    for var in variations:
        ann = annotation_map.get(var.id)
        nodes[var.id] = VariationNode(
            move_number=var.move_number,
            color=var.color,
            san=var.san,
            uci=var.uci,
            fen=var.fen,
            nag=ann.nag if ann else None,
            comment=ann.text if ann else None,
            rank=var.rank,
        )
        children[var.parent_id].append(var)

    # Attach children to their parent nodes in rank order.
    for parent_id, items in children.items():
        if parent_id is None:
            continue
        parent_node = nodes.get(parent_id)
        if not parent_node:
            continue
        for child in sorted(items, key=lambda v: v.rank):
            parent_node.children.append(nodes[child.id])

    # Choose mainline root and attach alternative first moves as variations.
    root_candidates = sorted(children.get(None, []), key=lambda v: v.rank)
    if not root_candidates:
        return None
    main_root = root_candidates[0]
    root_node = nodes[main_root.id]
    for alt in root_candidates[1:]:
        alt_node = nodes[alt.id]
        if alt_node.rank == 0:
            alt_node.rank = max(1, alt.rank)
        root_node.children.append(alt_node)

    return root_node


def build_mainline_moves(
    variations: Iterable[Variation],
    annotations: Iterable[MoveAnnotation],
) -> list[dict[str, object]]:
    """Build a flat mainline move list for UI rendering."""
    variations = list(variations)
    annotation_map = {ann.move_id: ann for ann in annotations}
    children: dict[str | None, list[Variation]] = defaultdict(list)
    for var in variations:
        children[var.parent_id].append(var)

    roots = sorted(children.get(None, []), key=lambda v: v.rank)
    current = roots[0] if roots else None
    mainline: list[dict[str, object]] = []

    while current:
        ann = annotation_map.get(current.id)
        mainline.append(
            {
                "id": current.id,
                "move_number": current.move_number,
                "color": current.color,
                "san": current.san,
                "fen": current.fen,
                "annotation_id": ann.id if ann else None,
                "annotation_text": ann.text if ann else None,
                "annotation_version": ann.version if ann else None,
            }
        )
        next_moves = [v for v in children.get(current.id, []) if v.rank == 0]
        current = next_moves[0] if next_moves else None

    return mainline
