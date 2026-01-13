from workspace.pgn.serializer.to_tree import pgn_to_tree, VariationNode
from workspace.pgn.cleaner.variation_pruner import find_node_by_path

PGN_SAMPLE = """
[Event "Test Game"]

1. e4 (1. d4 d5 2. c4) e5 (1...c5 2. Nf3) 2. Nf3 (2. Bc4) Nc6 3. Bb5 *
"""

tree = pgn_to_tree(PGN_SAMPLE)
print(f"Tree: {tree}")
if tree:
    print(f"Children: {len(tree.children)}")
    for child in tree.children:
        print(f" - {child.san} (rank={child.rank})")
        if child.children:
             print(f"   - {child.children[0].san}")

node = find_node_by_path(tree, "main.2")
print(f"Node main.2: {node}")
