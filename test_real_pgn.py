import sys
from pathlib import Path
import chess.pgn
from io import StringIO

# Add backend directory to path
backend_dir = Path("/home/catadragon/Code/catachess/backend/modules")
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from workspace.pgn.serializer.to_tree import pgn_to_tree
from workspace.pgn.serializer.to_pgn import tree_to_pgn
from workspace.pgn.cleaner.no_comment_pgn import export_no_comment_pgn

PGN_FILE = "/home/catadragon/Code/catachess/1.d4 Nf6 2.c4 e6 3.Bf4 - Complete Repertoire for White - GM Davorin Kuljasevic.pgn"

def test_large_pgn():
    with open(PGN_FILE, "r", encoding="utf-8") as f:
        pgn_content = f.read()
    
    # Split content into individual games (python-chess can read multiple games from one file)
    pgn_io = StringIO(pgn_content)
    game_count = 0
    
    while True:
        # Use StringIO for each game to mimic how our service handles individual chapter PGNs
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
        
        game_count += 1
        print(f"Processing game {game_count}: {game.headers.get('Title', 'No Title')}")
        
        # Convert back to PGN string for our parser
        game_str = str(game)
        
        try:
            # Parse to tree
            tree = pgn_to_tree(game_str)
            if not tree:
                print(f" - Game {game_count} has no moves")
                continue
            
            # Serialize back to PGN
            serialized = tree_to_pgn(tree, headers=tree.headers)
            print(f" - Serialized length: {len(serialized)}")
            
            # Test no-comment export (which uses recursion in pruner)
            no_comment = export_no_comment_pgn(tree, include_headers=False)
            print(f" - No-comment length: {len(no_comment)}")
            
        except Exception as e:
            print(f" ! Error processing game {game_count}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Stop on first error for debugging
            sys.exit(1)

    print(f"\nSuccessfully processed {game_count} games from the PGN file.")

if __name__ == "__main__":
    test_large_pgn()
