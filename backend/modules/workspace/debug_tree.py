#!/usr/bin/env python3
"""Debug script to understand tree structure."""

from workspace.pgn.serializer.to_tree import pgn_to_tree


def print_tree(node, depth=0, label=""):
    """Print tree structure recursively."""
    indent = "  " * depth
    move_info = f"{node.move_number}{'.' if node.color == 'white' else '...'}{node.san}"
    print(f"{indent}{label}{move_info} (rank={node.rank}, children={len(node.children)})")

    for i, child in enumerate(node.children):
        child_label = f"[{child.rank}] " if len(node.children) > 1 else ""
        print_tree(child, depth + 1, child_label)


if __name__ == "__main__":
    pgn = """
[Event "Test Game"]

1. e4 (1. d4 d5 2. c4) e5 (1...c5 2. Nf3) 2. Nf3 (2. Bc4) Nc6 3. Bb5 *
"""

    print("Parsing PGN:")
    print(pgn)
    print("\nTree structure:")
    tree = pgn_to_tree(pgn)
    if tree:
        print_tree(tree)
    else:
        print("No tree generated")
