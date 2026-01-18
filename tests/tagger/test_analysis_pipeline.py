"""
Integration tests for the analysis pipeline.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from backend.core.tagger.analysis.pipeline import AnalysisPipeline


class TestAnalysisPipeline:
    """Test the full analysis pipeline."""

    @pytest.fixture
    def sample_pgn(self):
        """Create a temporary PGN file for testing."""
        pgn_content = """[Event "Test"]
[Site "Test"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pgn', delete=False) as f:
            f.write(pgn_content)
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink()

    @pytest.fixture
    def output_dir(self):
        """Create temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir

        # Cleanup
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()

    def test_pipeline_initialization(self, sample_pgn, output_dir):
        """Test pipeline initialization."""
        pipeline = AnalysisPipeline(
            pgn_path=sample_pgn,
            output_dir=output_dir,
        )

        assert pipeline.pgn_path == sample_pgn
        assert pipeline.output_dir == output_dir
        assert output_dir.exists()

    @pytest.mark.skipif(
        not Path("/usr/games/stockfish").exists()
        or os.getenv("ALLOW_STOCKFISH_TESTS") != "1",
        reason="Stockfish tests disabled"
    )
    def test_pipeline_run_with_max_positions(self, sample_pgn, output_dir):
        """Test running pipeline with position limit."""
        pipeline = AnalysisPipeline(
            pgn_path=sample_pgn,
            output_dir=output_dir,
            engine_mode="local",
        )

        # Only analyze 2 positions
        stats = pipeline.run(verbose=False, max_positions=2)

        assert stats.total_positions == 2
        assert len(stats.tag_counts) > 0

    @pytest.mark.skipif(
        not Path("/usr/games/stockfish").exists()
        or os.getenv("ALLOW_STOCKFISH_TESTS") != "1",
        reason="Stockfish tests disabled"
    )
    def test_pipeline_run_and_save(self, sample_pgn, output_dir):
        """Test running pipeline and saving output."""
        pipeline = AnalysisPipeline(
            pgn_path=sample_pgn,
            output_dir=output_dir,
            engine_mode="local",
        )

        # Run and save with max 2 positions
        stats = pipeline.run_and_save(
            verbose=False,
            max_positions=2,
            save_json=True,
            save_txt=True,
        )

        # Check output files were created
        json_files = list(output_dir.glob("*.json"))
        txt_files = list(output_dir.glob("*.txt"))

        assert len(json_files) == 1
        assert len(txt_files) == 1

        # Verify JSON content
        with open(json_files[0]) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "tag_counts" in data
        assert "tag_percentages" in data
        assert data["metadata"]["total_positions"] == 2

        # Verify text content
        with open(txt_files[0]) as f:
            content = f.read()

        assert "TAG STATISTICS REPORT" in content
        assert "Total Positions Analyzed: 2" in content

    def test_skip_opening_moves(self, sample_pgn, output_dir):
        """Test skipping opening moves."""
        pipeline = AnalysisPipeline(
            pgn_path=sample_pgn,
            output_dir=output_dir,
            skip_opening_moves=1,
        )

        assert pipeline.skip_opening_moves == 1

    def test_custom_engine_params(self, sample_pgn, output_dir):
        """Test custom engine parameters."""
        pipeline = AnalysisPipeline(
            pgn_path=sample_pgn,
            output_dir=output_dir,
            depth=10,
            multipv=3,
        )

        assert pipeline.depth == 10
        assert pipeline.multipv == 3
