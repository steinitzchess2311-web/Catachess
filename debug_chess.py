import chess.pgn
from io import StringIO

pgn = "1. e4 e5 2. Nf3 (2. Bc4) Nc6 3. Bb5 *"
game = chess.pgn.read_game(StringIO(pgn))
e4 = game.next()
e5 = e4.next()
nf3 = e5.next()
print(f"nf3: {nf3.move}")
print(f"nf3 variations: {[v.move for v in nf3.variations]}")
# Expect nf3.variations[0] to be Nc6, and variations[1] to be Bc4?
# OR is Bc4 an alternative to Nf3?
# If pgn is "2. Nf3 (2. Bc4) Nc6", then Bc4 is an alternative to Nf3.
# Let's check e5 variations.
print(f"e5 variations: {[v.move for v in e5.variations]}")
