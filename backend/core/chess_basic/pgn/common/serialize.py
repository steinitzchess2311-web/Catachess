"""
chess_basic.pgn.common.serialize
PGN 文本序列化逻辑

PGN text serialization logic.
"""

from typing import Optional
from .pgn_types import PGNNode, PGNMove, NAG_SYMBOLS


def serialize_tags(tags: dict[str, str]) -> str:
    """
    序列化标签为 PGN 格式
    Serialize tags to PGN format

    Args:
        tags: Dictionary of tags

    Returns:
        PGN tag section string
    """
    lines = []

    # 七标签名册按顺序 Seven Tag Roster in order
    roster_order = ["Event", "Site", "Date", "Round", "White", "Black", "Result"]
    for key in roster_order:
        if key in tags:
            lines.append(f'[{key} "{tags[key]}"]')

    # 其他标签 Other tags
    for key, value in sorted(tags.items()):
        if key not in roster_order:
            lines.append(f'[{key} "{value}"]')

    return "\n".join(lines)


def serialize_moves_mainline(
    nodes: list[PGNNode],
    starting_move_number: int = 1,
    starting_color_white: bool = True,
) -> str:
    """
    序列化主线走法为 PGN 格式（不包含分支）
    Serialize mainline moves to PGN format (without variations)

    Args:
        nodes: List of move nodes
        starting_move_number: Starting move number
        starting_color_white: Whether starting with white's move

    Returns:
        PGN movetext string
    """
    if not nodes:
        return "*"

    lines = []
    current_line = ""
    move_number = starting_move_number
    is_white = starting_color_white

    for i, node in enumerate(nodes):
        move = node.move

        # 添加回合号 Add move number
        if is_white:
            move_str = f"{move_number}. {move.san}"
        else:
            # 只在需要时添加黑方回合号 Only add black move number when needed
            if i == 0:
                move_str = f"{move_number}... {move.san}"
            else:
                move_str = move.san

        # 添加 NAG Add NAGs
        for nag in move.nags:
            if nag in NAG_SYMBOLS:
                move_str += NAG_SYMBOLS[nag]
            else:
                move_str += f"${nag}"

        # 添加评注 Add comment
        if move.comment:
            move_str += f" {{ {move.comment} }}"

        # 换行控制（每行约 80 字符）Line break control (approx 80 chars per line)
        if len(current_line) + len(move_str) + 1 > 80:
            lines.append(current_line)
            current_line = move_str
        else:
            if current_line:
                current_line += " " + move_str
            else:
                current_line = move_str

        # 更新状态 Update state
        if not is_white:
            move_number += 1
        is_white = not is_white

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


def serialize_comment(comment: str) -> str:
    """
    序列化评注
    Serialize comment

    Args:
        comment: Comment text

    Returns:
        PGN comment string
    """
    # 转义大括号 Escape braces
    comment = comment.replace("}", "\\}")
    return f"{{ {comment} }}"


def format_nag(nag: int) -> str:
    """
    格式化 NAG
    Format NAG

    Args:
        nag: Numeric Annotation Glyph

    Returns:
        NAG string
    """
    if nag in NAG_SYMBOLS:
        return NAG_SYMBOLS[nag]
    return f"${nag}"


def wrap_text(text: str, max_line_length: int = 80) -> str:
    """
    将文本按指定长度换行
    Wrap text to specified length

    Args:
        text: Text to wrap
        max_line_length: Maximum line length

    Returns:
        Wrapped text
    """
    if len(text) <= max_line_length:
        return text

    lines = []
    current_line = ""
    words = text.split()

    for word in words:
        if len(current_line) + len(word) + 1 > max_line_length:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)
