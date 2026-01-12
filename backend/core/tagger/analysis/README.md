# PGN Tag Analysis Pipeline

This pipeline analyzes PGN chess files and calculates the percentage occurrence of each tag across all positions in the games.

## Installation

Ensure you have Stockfish installed:

```bash
# Ubuntu/Debian
sudo apt-get install stockfish

# macOS
brew install stockfish
```

## Directory Structure

```
backend/core/tagger/
├── analysis/          # Analysis pipeline code
│   ├── __init__.py
│   ├── cli.py        # Command-line interface
│   ├── pgn_processor.py
│   ├── pipeline.py
│   └── tag_statistics.py
├── data/
│   ├── pgn/          # Input PGN files (put your files here)
│   └── output/       # Output statistics files
```

## Usage

### Command Line

Basic usage:

```bash
# Analyze a PGN file
python -m backend.core.tagger.analysis.cli backend/core/tagger/data/pgn/your_game.pgn

# With custom output directory
python -m backend.core.tagger.analysis.cli your_game.pgn --output-dir custom_output/

# Limit number of positions (useful for testing)
python -m backend.core.tagger.analysis.cli your_game.pgn --max-positions 100

# Skip opening moves (e.g., skip first 5 moves)
python -m backend.core.tagger.analysis.cli your_game.pgn --skip-opening-moves 5

# Custom engine settings
python -m backend.core.tagger.analysis.cli your_game.pgn \
    --engine-path /usr/local/bin/stockfish \
    --depth 20 \
    --multipv 8
```

### Python API

```python
from backend.core.tagger.analysis import AnalysisPipeline

# Create pipeline
pipeline = AnalysisPipeline(
    pgn_path="backend/core/tagger/data/pgn/my_games.pgn",
    output_dir="backend/core/tagger/data/output",
    depth=14,  # Engine depth
    multipv=6,  # Number of variations
    skip_opening_moves=0,  # Skip N opening moves
)

# Run and save results
stats = pipeline.run_and_save(
    verbose=True,
    max_positions=None,  # None = analyze all
    save_json=True,
    save_txt=True,
)

# Access statistics
print(f"Total positions: {stats.total_positions}")
for tag, percentage, count in stats.get_sorted_percentages():
    print(f"{tag}: {percentage:.2f}% ({count} occurrences)")
```

## Output Files

The pipeline generates two types of output files:

### 1. Text Report (`*_stats_TIMESTAMP.txt`)

Human-readable report with:
- Total positions analyzed
- Tag occurrences sorted by frequency
- Percentages for each tag

Example:
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
...
```

### 2. JSON Data (`*_stats_TIMESTAMP.json`)

Machine-readable data with:
- Metadata (file info, settings, timestamp)
- Tag counts
- Tag percentages

Example:
```json
{
  "metadata": {
    "pgn_file": "games.pgn",
    "timestamp": "20240101_120000",
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

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `pgn_file` | Path to input PGN file | Required |
| `--output-dir` | Output directory | `backend/core/tagger/data/output` |
| `--engine-path` | Path to Stockfish | `/usr/games/stockfish` |
| `--depth` | Engine analysis depth | 14 |
| `--multipv` | Number of variations | 6 |
| `--skip-opening-moves` | Skip N opening moves | 0 |
| `--max-positions` | Max positions to analyze | All |
| `--no-json` | Don't save JSON output | False |
| `--no-txt` | Don't save text report | False |
| `--quiet` | Suppress progress output | False |

## Performance Tips

1. **Limit positions for testing**: Use `--max-positions 100` to quickly test the pipeline
2. **Skip opening moves**: Use `--skip-opening-moves 5` to focus on middlegame/endgame
3. **Reduce depth**: Lower `--depth` for faster analysis (less accurate)
4. **Reduce multipv**: Lower `--multipv` for faster analysis

## Example Workflow

```bash
# 1. Place your PGN file in the data directory
cp my_games.pgn backend/core/tagger/data/pgn/

# 2. Run quick test on first 50 positions
python -m backend.core.tagger.analysis.cli \
    backend/core/tagger/data/pgn/my_games.pgn \
    --max-positions 50

# 3. Run full analysis
python -m backend.core.tagger.analysis.cli \
    backend/core/tagger/data/pgn/my_games.pgn

# 4. Check results
ls -lh backend/core/tagger/data/output/
cat backend/core/tagger/data/output/my_games_stats_*.txt
```

## Testing

Run the test suite:

```bash
# Run all tagger tests
pytest tests/tagger/

# Run specific test file
pytest tests/tagger/test_pgn_processor.py

# Run with coverage
pytest tests/tagger/ --cov=backend.core.tagger.analysis
```

## Troubleshooting

### "Stockfish engine not found"

Install Stockfish or specify the path:
```bash
python -m backend.core.tagger.analysis.cli game.pgn --engine-path /path/to/stockfish
```

### "PGN file not found"

Use absolute path or path relative to project root:
```bash
python -m backend.core.tagger.analysis.cli backend/core/tagger/data/pgn/game.pgn
```

### Analysis is too slow

Reduce depth and multipv:
```bash
python -m backend.core.tagger.analysis.cli game.pgn --depth 10 --multipv 3
```
