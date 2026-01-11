"""
chess_basic.pgn.common.io
PGN 字符串/文件输出工具

PGN string/file output utilities.
"""

from pathlib import Path
from typing import Optional


def write_pgn_to_string(tags: dict[str, str], movetext: str, result: Optional[str] = None) -> str:
    """
    组装完整的 PGN 字符串
    Assemble complete PGN string

    Args:
        tags: PGN tags
        movetext: PGN movetext
        result: Game result (appended to movetext if provided)

    Returns:
        Complete PGN string
    """
    from .serialize import serialize_tags

    pgn_parts = []

    # 标签部分 Tags section
    tags_str = serialize_tags(tags)
    if tags_str:
        pgn_parts.append(tags_str)

    # 空行分隔标签和走法 Empty line between tags and moves
    pgn_parts.append("")

    # 走法部分 Movetext section
    if result and not movetext.strip().endswith(result):
        movetext = movetext.strip() + " " + result
    pgn_parts.append(movetext)

    return "\n".join(pgn_parts)


def write_pgn_to_file(pgn_string: str, filepath: str, append: bool = False) -> None:
    """
    将 PGN 字符串写入文件
    Write PGN string to file

    Args:
        pgn_string: Complete PGN string
        filepath: Path to output file
        append: If True, append to file; if False, overwrite
    """
    mode = "a" if append else "w"
    path = Path(filepath)

    # 确保父目录存在 Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode, encoding="utf-8") as f:
        f.write(pgn_string)
        # PGN 游戏之间需要双换行 Double newline between PGN games
        if append:
            f.write("\n\n")


def read_pgn_from_file(filepath: str) -> str:
    """
    从文件读取 PGN 字符串
    Read PGN string from file

    Args:
        filepath: Path to PGN file

    Returns:
        PGN file contents
    """
    path = Path(filepath)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def append_pgn_to_file(pgn_string: str, filepath: str) -> None:
    """
    追加 PGN 到文件
    Append PGN to file

    Args:
        pgn_string: Complete PGN string
        filepath: Path to output file
    """
    write_pgn_to_file(pgn_string, filepath, append=True)
