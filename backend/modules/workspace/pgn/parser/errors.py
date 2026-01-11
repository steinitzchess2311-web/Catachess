"""
PGN parsing errors.

Defines error types and provides error location information.
"""


class PGNParseError(Exception):
    """Base exception for PGN parsing errors."""

    def __init__(
        self,
        message: str,
        line_number: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ):
        """
        Initialize parse error.

        Args:
            message: Error message
            line_number: Line number where error occurred
            column: Column where error occurred
            context: Surrounding text for context
        """
        self.message = message
        self.line_number = line_number
        self.column = column
        self.context = context

        # Build full error message
        full_message = message
        if line_number is not None:
            full_message += f" at line {line_number}"
            if column is not None:
                full_message += f", column {column}"
        if context:
            full_message += f"\nContext: {context}"

        super().__init__(full_message)


class InvalidPGNFormatError(PGNParseError):
    """PGN format is invalid or corrupted."""

    pass


class MissingHeaderError(PGNParseError):
    """Required PGN header is missing."""

    pass


class InvalidMoveError(PGNParseError):
    """Move notation is invalid."""

    pass


class EmptyPGNError(PGNParseError):
    """PGN content is empty or contains no games."""

    pass


class EncodingError(PGNParseError):
    """PGN encoding is invalid or unsupported."""

    pass
