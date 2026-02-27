"""Core planning logic for Opening Trainer eligibility and unit splitting."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import random
import secrets
from typing import Any, Callable


STANDARD_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MAX_SPLIT_PLY = 8
MIN_ELIGIBLE_PLY = 5


@dataclass(frozen=True)
class TrainerStep:
    state_id: str
    from_fen: str
    to_state_id: str
    to_fen: str
    san: str
    uci: str
    color: str
    move_number: int
    ply: int
    chapter_id: str
    step_key: str


def normalize_fen_key(fen: str | None) -> str:
    """Normalize FEN into a stable key for transposition and progress matching."""
    value = (fen or "").strip()
    if not value:
        return value
    parts = value.split()
    if len(parts) >= 4:
        return " ".join(parts[:4])
    return value


def is_standard_start_fen(fen: str | None) -> bool:
    if fen is None:
        return True
    return normalize_fen_key(fen) == normalize_fen_key(STANDARD_START_FEN)


def _ply_of(move_number: int, color: str) -> int:
    return move_number * 2 - (1 if color == "white" else 0)


def _chapter_root_state_id(chapter_id: str) -> str:
    return f"chapter:{chapter_id}:root"


def _move_label(move_number: int, color: str, san: str) -> str:
    if color == "white":
        return f"{move_number}.{san}"
    return f"{move_number}...{san}"


def _step_sort_key(step: TrainerStep) -> tuple[Any, ...]:
    color_order = 0 if step.color == "white" else 1
    return (step.ply, step.move_number, color_order, step.san, step.from_fen, step.to_fen)


def _node_id(prefix: str, payload: str) -> str:
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _build_children_by_parent(variations: list[Any]) -> dict[str | None, list[Any]]:
    children_by_parent: dict[str | None, list[Any]] = defaultdict(list)
    for variation in variations:
        children_by_parent[getattr(variation, "parent_id", None)].append(variation)
    for siblings in children_by_parent.values():
        siblings.sort(key=lambda item: (getattr(item, "rank", 0), getattr(item, "san", ""), getattr(item, "id", "")))
    return children_by_parent


def _max_line_ply_for_chapter(variations: list[Any]) -> int:
    children_by_parent = _build_children_by_parent(variations)

    def dfs(parent_id: str | None, depth: int) -> int:
        children = children_by_parent.get(parent_id, [])
        if not children:
            return depth
        return max(dfs(getattr(child, "id"), depth + 1) for child in children)

    return dfs(None, 0)


def build_eligibility_summary(chapters: list[Any], variations_by_chapter: dict[str, list[Any]]) -> dict[str, Any]:
    total_chapters = len(chapters)
    standard_chapters = [chapter for chapter in chapters if is_standard_start_fen(getattr(chapter, "starting_fen", None))]
    trainable_chapters = []
    max_line_ply = 0
    lines_ge_min_ply = 0

    for chapter in standard_chapters:
        chapter_id = getattr(chapter, "id")
        variations = variations_by_chapter.get(chapter_id, [])
        if not variations:
            continue
        trainable_chapters.append(chapter_id)
        chapter_max_ply = _max_line_ply_for_chapter(variations)
        max_line_ply = max(max_line_ply, chapter_max_ply)
        if chapter_max_ply >= MIN_ELIGIBLE_PLY:
            lines_ge_min_ply += 1

    reasons: list[str] = []
    if not standard_chapters:
        reasons.append("No chapter starts from standard initial position")
    if not trainable_chapters:
        reasons.append("No moves found in standard-start chapters")
    if max_line_ply < MIN_ELIGIBLE_PLY:
        reasons.append(f"No standard-start variation line reaches {MIN_ELIGIBLE_PLY}+ plies")

    eligible = not reasons
    return {
        "eligible": eligible,
        "reasons": reasons,
        "stats": {
            "total_chapters": total_chapters,
            "standard_start_chapters": len(standard_chapters),
            "trainable_chapters": len(trainable_chapters),
            "max_line_ply": max_line_ply,
            "lines_ge_5_ply": lines_ge_min_ply,
        },
        "trainable_chapter_ids": trainable_chapters,
    }


def _extract_chapter_lines(
    chapter: Any,
    variations: list[Any],
    *,
    mode: str,
) -> list[list[TrainerStep]]:
    chapter_id = getattr(chapter, "id")
    children_by_parent = _build_children_by_parent(variations)
    root_state_id = _chapter_root_state_id(chapter_id)
    chapter_start_fen = getattr(chapter, "starting_fen", None) or STANDARD_START_FEN

    lines: list[list[TrainerStep]] = []

    def dfs(parent_id: str | None, current_fen: str, path_steps: list[TrainerStep]) -> None:
        siblings = children_by_parent.get(parent_id, [])
        if not siblings:
            if path_steps:
                lines.append(list(path_steps))
            return

        if mode == "merged":
            state_id = normalize_fen_key(current_fen)
        else:
            state_id = root_state_id if parent_id is None else parent_id

        from_fen = normalize_fen_key(current_fen)

        for child in siblings:
            child_fen = getattr(child, "fen", "") or current_fen
            to_fen = normalize_fen_key(child_fen)
            to_state_id = to_fen if mode == "merged" else getattr(child, "id")
            move_number = getattr(child, "move_number", 1)
            color = getattr(child, "color", "white")
            san = getattr(child, "san", "")
            uci = getattr(child, "uci", "")
            ply = _ply_of(move_number, color)
            step_key = f"{state_id}|{color}|{san}|{to_state_id}|{ply}"

            step = TrainerStep(
                state_id=state_id,
                from_fen=from_fen,
                to_state_id=to_state_id,
                to_fen=to_fen,
                san=san,
                uci=uci,
                color=color,
                move_number=move_number,
                ply=ply,
                chapter_id=chapter_id,
                step_key=step_key,
            )
            path_steps.append(step)
            dfs(getattr(child, "id"), child_fen, path_steps)
            path_steps.pop()

    dfs(None, chapter_start_fen, [])
    return lines


def _line_signature(line: list[TrainerStep]) -> str:
    return "||".join(step.step_key for step in line)


def _find_next_split_state(active_lines: list[list[TrainerStep]], opponent_color: str) -> tuple[str, list[TrainerStep]] | None:
    if not active_lines:
        return None

    state_presence: dict[str, int] = defaultdict(int)
    state_options: dict[str, set[str]] = defaultdict(set)
    state_min_ply: dict[str, int] = {}
    option_ref: dict[str, TrainerStep] = {}

    for line in active_lines:
        seen_in_line: set[str] = set()
        for step in line:
            if step.color != opponent_color or step.ply > MAX_SPLIT_PLY:
                continue
            state_id = step.state_id
            if state_id in seen_in_line:
                continue
            seen_in_line.add(state_id)
            state_presence[state_id] += 1
            state_options[state_id].add(step.step_key)
            option_ref.setdefault(step.step_key, step)
            current_min = state_min_ply.get(state_id)
            if current_min is None or step.ply < current_min:
                state_min_ply[state_id] = step.ply

    total_lines = len(active_lines)
    candidates = [
        state_id
        for state_id, options in state_options.items()
        if len(options) >= 2 and state_presence.get(state_id, 0) == total_lines
    ]
    if not candidates:
        return None

    selected_state = sorted(candidates, key=lambda sid: (state_min_ply.get(sid, 999), sid))[0]
    selected_options = sorted(
        (option_ref[opt_key] for opt_key in state_options[selected_state]),
        key=_step_sort_key,
    )
    return selected_state, selected_options


def _line_option_for_state(line: list[TrainerStep], state_id: str, opponent_color: str) -> str | None:
    for step in line:
        if step.state_id == state_id and step.color == opponent_color and step.ply <= MAX_SPLIT_PLY:
            return step.step_key
    return None


def _build_leaf_node(
    lines: list[list[TrainerStep]],
    trainee_color: str,
    path_labels: list[str],
    *,
    chapter_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    required_by_key: dict[str, TrainerStep] = {}
    for line in lines:
        for step in line:
            if step.color == trainee_color:
                required_by_key.setdefault(step.step_key, step)
    required_steps = sorted(required_by_key.values(), key=_step_sort_key)

    required_moves = [
        {
            "from_fen": step.from_fen,
            "move_san": step.san,
            "move_uci": step.uci,
            "color": step.color,
            "move_number": step.move_number,
            "ply": step.ply,
        }
        for step in required_steps
    ]
    line_payloads = []
    for line in sorted(lines, key=_line_signature):
        line_payloads.append(
            {
                "signature": _line_signature(line),
                "steps": [
                    {
                        "from_fen": step.from_fen,
                        "to_fen": step.to_fen,
                        "move_san": step.san,
                        "move_uci": step.uci,
                        "color": step.color,
                        "move_number": step.move_number,
                        "ply": step.ply,
                    }
                    for step in line
                ],
            }
        )
    required_fens = sorted({step.from_fen for step in required_steps})
    line_count = len(lines)
    max_ply = max((max((step.ply for step in line), default=0) for line in lines), default=0)
    path_display = " / ".join(path_labels)
    leaf_title = path_display or "Unit"
    leaf_id = _node_id(
        "ot_unit",
        f"{chapter_id or 'merged'}::{trainee_color}::{path_display}::{line_count}::{max_ply}",
    )

    node = {
        "id": leaf_id,
        "kind": "unit",
        "title": leaf_title,
        "edge_label": path_labels[-1] if path_labels else None,
        "chapter_id": chapter_id,
        "line_count": line_count,
        "max_ply": max_ply,
        "required_move_count": len(required_moves),
        "required_fens": required_fens,
        "required_moves": required_moves,
        "children": [],
    }
    leaf_summary = {
        "id": leaf_id,
        "title": leaf_title,
        "chapter_id": chapter_id,
        "line_count": line_count,
        "max_ply": max_ply,
        "required_move_count": len(required_moves),
        "required_fens": required_fens,
        "required_moves": required_moves,
        "path": path_labels,
        "_lines": line_payloads,
    }
    return node, leaf_summary


def _build_unit_tree(
    lines: list[list[TrainerStep]],
    trainee_color: str,
    *,
    chapter_id: str | None,
    path_labels: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if path_labels is None:
        path_labels = []
    opponent_color = "black" if trainee_color == "white" else "white"

    split_info = _find_next_split_state(lines, opponent_color=opponent_color)
    if split_info is None:
        leaf_node, leaf_summary = _build_leaf_node(
            lines,
            trainee_color=trainee_color,
            path_labels=path_labels,
            chapter_id=chapter_id,
        )
        return leaf_node, [leaf_summary]

    split_state, options = split_info
    split_ply = min(step.ply for step in options)
    split_node = {
        "id": _node_id("ot_split", f"{chapter_id or 'merged'}::{split_state}::{split_ply}::{','.join(path_labels)}"),
        "kind": "split",
        "title": f"Opponent choices (ply {split_ply})",
        "edge_label": path_labels[-1] if path_labels else None,
        "chapter_id": chapter_id,
        "line_count": len(lines),
        "max_ply": max((max((step.ply for step in line), default=0) for line in lines), default=0),
        "required_move_count": 0,
        "required_fens": [],
        "required_moves": [],
        "children": [],
    }

    leaves: list[dict[str, Any]] = []
    for option in options:
        move_label = _move_label(option.move_number, option.color, option.san)
        filtered_lines = [
            line
            for line in lines
            if _line_option_for_state(line, split_state, opponent_color=opponent_color) == option.step_key
        ]
        if not filtered_lines:
            continue
        child_node, child_leaves = _build_unit_tree(
            filtered_lines,
            trainee_color=trainee_color,
            chapter_id=chapter_id,
            path_labels=[*path_labels, move_label],
        )
        if child_node.get("edge_label") is None:
            child_node["edge_label"] = move_label
        split_node["children"].append(child_node)
        leaves.extend(child_leaves)

    return split_node, leaves


def build_unit_catalog(
    *,
    study_id: str,
    mode: str,
    trainee_color: str,
    chapters: list[Any],
    variations_by_chapter: dict[str, list[Any]],
) -> dict[str, Any]:
    eligibility = build_eligibility_summary(chapters, variations_by_chapter)
    trainable_ids = set(eligibility["trainable_chapter_ids"])
    trainable_chapters = [chapter for chapter in chapters if getattr(chapter, "id") in trainable_ids]

    roots: list[dict[str, Any]] = []
    leaf_units: list[dict[str, Any]] = []

    if mode == "chapter":
        for chapter in trainable_chapters:
            chapter_id = getattr(chapter, "id")
            title = getattr(chapter, "title", None) or f"Chapter {chapter_id}"
            chapter_lines = _extract_chapter_lines(
                chapter,
                variations_by_chapter.get(chapter_id, []),
                mode="chapter",
            )
            if not chapter_lines:
                continue

            subtree, subtree_leaves = _build_unit_tree(
                chapter_lines,
                trainee_color=trainee_color,
                chapter_id=chapter_id,
            )
            chapter_node = {
                "id": _node_id("ot_chapter", chapter_id),
                "kind": "chapter",
                "title": title,
                "edge_label": None,
                "chapter_id": chapter_id,
                "line_count": len(chapter_lines),
                "max_ply": max((max((step.ply for step in line), default=0) for line in chapter_lines), default=0),
                "required_move_count": 0,
                "required_fens": [],
                "required_moves": [],
                "children": [subtree],
            }
            roots.append(chapter_node)
            leaf_units.extend(subtree_leaves)
    else:
        merged_lines: list[list[TrainerStep]] = []
        line_signatures: set[str] = set()
        for chapter in trainable_chapters:
            chapter_id = getattr(chapter, "id")
            lines = _extract_chapter_lines(
                chapter,
                variations_by_chapter.get(chapter_id, []),
                mode="merged",
            )
            for line in lines:
                signature = _line_signature(line)
                if signature in line_signatures:
                    continue
                line_signatures.add(signature)
                merged_lines.append(line)

        if merged_lines:
            merged_tree, merged_leaves = _build_unit_tree(
                merged_lines,
                trainee_color=trainee_color,
                chapter_id=None,
            )
            roots.append(
                {
                    "id": _node_id("ot_merged", study_id),
                    "kind": "merged",
                    "title": "Merged Repertoire",
                    "edge_label": None,
                    "chapter_id": None,
                    "line_count": len(merged_lines),
                    "max_ply": max((max((step.ply for step in line), default=0) for line in merged_lines), default=0),
                    "required_move_count": 0,
                    "required_fens": [],
                    "required_moves": [],
                    "children": [merged_tree],
                }
            )
            leaf_units.extend(merged_leaves)

    return {
        "study_id": study_id,
        "mode": mode,
        "color": trainee_color,
        "eligibility": {
            "eligible": eligibility["eligible"],
            "reasons": eligibility["reasons"],
            "stats": eligibility["stats"],
        },
        "roots": roots,
        "leaf_units": leaf_units,
        "total_units": len(leaf_units),
    }


def normalize_san_for_compare(san: str | None) -> str:
    value = (san or "").strip()
    if not value:
        return value
    value = value.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    while value and value[-1] in {"+", "#", "!", "?"}:
        value = value[:-1]
    return value


def get_leaf_unit(catalog: dict[str, Any], unit_id: str | None = None) -> dict[str, Any] | None:
    leaf_units = list(catalog.get("leaf_units") or [])
    if not leaf_units:
        return None
    if unit_id:
        for unit in leaf_units:
            if unit.get("id") == unit_id:
                return unit
        return None
    return sorted(leaf_units, key=lambda unit: (unit.get("chapter_id") or "", "/".join(unit.get("path") or []), unit.get("title") or ""))[0]


def pick_line_for_unit(unit: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
    lines = list(unit.get("_lines") or [])
    if not lines:
        raise ValueError("Unit has no playable lines")

    effective_seed = seed if seed is not None else secrets.randbelow(2**31)
    rng = random.Random(effective_seed)
    line_index = rng.randrange(len(lines))
    selected = lines[line_index]
    return {
        "seed": effective_seed,
        "line_index": line_index,
        "line_signature": selected["signature"],
        "line_count": len(lines),
        "steps": selected["steps"],
    }


def get_line_by_signature(unit: dict[str, Any], line_signature: str) -> list[dict[str, Any]] | None:
    for line in unit.get("_lines") or []:
        if line.get("signature") == line_signature:
            return line.get("steps") or []
    return None


def advance_until_prompt(
    *,
    line_steps: list[dict[str, Any]],
    start_index: int,
    trainee_color: str,
    is_mastered: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    idx = start_index
    auto_moves: list[dict[str, Any]] = []

    while idx < len(line_steps):
        step = line_steps[idx]
        step_color = step.get("color")
        if step_color != trainee_color:
            auto_moves.append(
                {
                    **step,
                    "reason": "opponent",
                }
            )
            idx += 1
            continue

        if is_mastered(step):
            auto_moves.append(
                {
                    **step,
                    "reason": "mastered_skip",
                }
            )
            idx += 1
            continue

        return {
            "next_index": idx,
            "auto_moves": auto_moves,
            "prompt": step,
            "finished": False,
        }

    return {
        "next_index": idx,
        "auto_moves": auto_moves,
        "prompt": None,
        "finished": True,
    }
