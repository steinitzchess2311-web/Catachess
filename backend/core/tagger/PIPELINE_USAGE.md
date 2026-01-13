# PGN Tag Analysis Pipeline - Quick Start

## Overview

The PGN tag analysis pipeline processes chess games from PGN files and calculates the percentage occurrence of each chess tag across all positions.

## Quick Start

### 1. Place your PGN file

```bash
cp your_games.pgn backend/core/tagger/data/pgn/
```

### 2. Run the analysis

```bash
cd backend/core/tagger
./venv/bin/python run_analysis.py data/pgn/your_games.pgn
```

### 3. Check results

Results are saved in `backend/core/tagger/data/output/`:
- `*_stats_TIMESTAMP.txt` - Human-readable report
- `*_stats_TIMESTAMP.json` - Machine-readable JSON data

## Command Options

```bash
# Analyze only first N positions (for testing)
./venv/bin/python run_analysis.py data/pgn/game.pgn --max-positions 100

# Skip opening moves
./venv/bin/python run_analysis.py data/pgn/game.pgn --skip-opening-moves 5

# Custom output directory
./venv/bin/python run_analysis.py data/pgn/game.pgn --output-dir custom_output/

# Faster analysis (lower depth)
./venv/bin/python run_analysis.py data/pgn/game.pgn --depth 10 --multipv 3

# Quiet mode (no progress output)
./venv/bin/python run_analysis.py data/pgn/game.pgn --quiet
```

## Example Output

### Text Report
```
================================================================================
TAG STATISTICS REPORT
================================================================================
Total Positions Analyzed: 500

Tag Occurrences (sorted by frequency):
--------------------------------------------------------------------------------
Tag Name                                           Count      Percentage
--------------------------------------------------------------------------------
first_choice                                         450          90.00%
tactical_sensitivity                                 125          25.00%
constructive_maneuver                                 89          17.80%
opening_central_pawn_move                             67          13.40%
...
```

### JSON Data
```json
{
  "metadata": {
    "pgn_file": "games.pgn",
    "timestamp": "20260112_185947",
    "total_positions": 500,
    "depth": 14,
    "multipv": 6
  },
  "tag_counts": {
    "first_choice": 450,
    "tactical_sensitivity": 125
  },
  "tag_percentages": {
    "first_choice": 90.0,
    "tactical_sensitivity": 25.0
  }
}
```

## Directory Structure

```
backend/core/tagger/
├── analysis/          # Pipeline code
│   ├── cli.py        # Command-line interface
│   ├── pipeline.py   # Main pipeline
│   ├── pgn_processor.py
│   └── tag_statistics.py
├── data/
│   ├── pgn/          # Input PGN files
│   └── output/       # Output statistics files
├── run_analysis.py   # Convenience script
└── PIPELINE_USAGE.md # This file
```

## Troubleshooting

### "Stockfish engine not found"
Install Stockfish:
```bash
sudo apt-get install stockfish  # Ubuntu/Debian
brew install stockfish          # macOS
```

Or specify custom path:
```bash
./venv/bin/python run_analysis.py game.pgn --engine-path /path/to/stockfish
```

### "PGN file not found"
Use path relative to tagger directory:
```bash
./venv/bin/python run_analysis.py data/pgn/your_game.pgn
```

### Analysis is too slow
Reduce depth and multipv:
```bash
./venv/bin/python run_analysis.py game.pgn --depth 10 --multipv 3
```

## Testing

Run tests:
```bash
cd /home/catadragon/Code/catachess
./venv/bin/python -m pytest tests/tagger/test_pgn_processor.py
./venv/bin/python -m pytest tests/tagger/test_tag_statistics.py
./venv/bin/python -m pytest tests/tagger/test_analysis_pipeline.py
```

## Full Documentation

See `backend/core/tagger/analysis/README.md` for complete documentation.
