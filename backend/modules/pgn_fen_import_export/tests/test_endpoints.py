"""
Tests for API Endpoints

Integration tests for FEN import endpoints.

Note: These tests require database and R2 mocking.
Run with: pytest backend/modules/pgn_fen_import_export/tests/test_endpoints.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from ..api.endpoints import import_from_fen
from ..api.schemas import FenImportRequest
from ..services.fen_validator import STANDARD_FEN


class TestImportFromFenEndpoint:
    """Tests for POST /fen/import endpoint."""

    @pytest.mark.asyncio
    async def test_import_custom_fen_success(self):
        """Test successful import of custom FEN position."""
        # Mock dependencies
        mock_study_repo = AsyncMock()
        mock_r2_client = Mock()

        # Mock study exists
        mock_study = Mock()
        mock_study.id = "study-123"
        mock_study_repo.get_study_by_id.return_value = mock_study

        # Mock no existing chapters
        mock_study_repo.get_chapters_by_study_id.return_value = []

        # Mock R2 upload
        mock_r2_client.upload_json.return_value = Mock(etag="etag-abc")

        # Request
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="Rook Endgame",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        )

        # Execute
        response = await import_from_fen(request, mock_study_repo, mock_r2_client)

        # Assertions
        assert response.chapter_id is not None
        assert response.starting_fen == "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        assert "successfully" in response.message.lower()

        # Verify calls
        mock_study_repo.create_chapter.assert_called_once()
        mock_study_repo.increment_chapter_count.assert_called_once_with("study-123")
        assert mock_study_repo.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_import_standard_fen_stores_null(self):
        """Test that standard FEN is stored as NULL."""
        # Mock dependencies
        mock_study_repo = AsyncMock()
        mock_r2_client = Mock()

        mock_study = Mock()
        mock_study.id = "study-123"
        mock_study_repo.get_study_by_id.return_value = mock_study
        mock_study_repo.get_chapters_by_study_id.return_value = []

        mock_r2_client.upload_json.return_value = Mock(etag="etag-abc")

        # Request with standard FEN
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="Standard Opening",
            fen=STANDARD_FEN
        )

        # Execute
        response = await import_from_fen(request, mock_study_repo, mock_r2_client)

        # Assert starting_fen is None (NULL in DB)
        assert response.starting_fen is None

    @pytest.mark.asyncio
    async def test_import_fails_if_study_not_found(self):
        """Test that import fails if study doesn't exist."""
        # Mock dependencies
        mock_study_repo = AsyncMock()
        mock_r2_client = Mock()

        # Mock study not found
        mock_study_repo.get_study_by_id.return_value = None

        # Request
        request = FenImportRequest(
            study_id="nonexistent-study",
            chapter_title="Test",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        )

        # Execute and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await import_from_fen(request, mock_study_repo, mock_r2_client)

        assert exc_info.value.status_code == 404
        assert "Study not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_import_sets_correct_chapter_order(self):
        """Test that chapter order is set correctly based on existing chapters."""
        # Mock dependencies
        mock_study_repo = AsyncMock()
        mock_r2_client = Mock()

        mock_study = Mock()
        mock_study.id = "study-123"
        mock_study_repo.get_study_by_id.return_value = mock_study

        # Mock 3 existing chapters
        existing_chapters = [Mock(), Mock(), Mock()]
        mock_study_repo.get_chapters_by_study_id.return_value = existing_chapters

        mock_r2_client.upload_json.return_value = Mock(etag="etag-abc")

        # Request
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="Fourth Chapter",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        )

        # Execute
        await import_from_fen(request, mock_study_repo, mock_r2_client)

        # Verify chapter was created with order=3 (0-indexed)
        call_args = mock_study_repo.create_chapter.call_args
        created_chapter = call_args[0][0]
        assert created_chapter.order == 3


class TestFenImportRequestValidation:
    """Tests for request body validation."""

    def test_valid_request(self):
        """Test that valid request is accepted."""
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="Test Chapter",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        )

        assert request.study_id == "study-123"
        assert request.chapter_title == "Test Chapter"
        assert request.fen == "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"

    def test_fen_gets_normalized(self):
        """Test that FEN with 4 parts gets normalized."""
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="Test",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq -"
        )

        # Should be normalized to 6 parts
        assert request.fen == "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"

    def test_invalid_fen_raises_validation_error(self):
        """Test that invalid FEN raises validation error."""
        with pytest.raises(ValueError, match="Invalid FEN"):
            FenImportRequest(
                study_id="study-123",
                chapter_title="Test",
                fen="invalid fen"
            )

    def test_empty_title_raises_validation_error(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            FenImportRequest(
                study_id="study-123",
                chapter_title="",
                fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
            )

    def test_title_too_long_raises_validation_error(self):
        """Test that overly long title raises validation error."""
        with pytest.raises(ValueError, match="too long"):
            FenImportRequest(
                study_id="study-123",
                chapter_title="x" * 201,  # Max 200
                fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
            )

    def test_whitespace_in_title_is_trimmed(self):
        """Test that leading/trailing whitespace is trimmed."""
        request = FenImportRequest(
            study_id="study-123",
            chapter_title="  Test Chapter  ",
            fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        )

        assert request.chapter_title == "Test Chapter"
