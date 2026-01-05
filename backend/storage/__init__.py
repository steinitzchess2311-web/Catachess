"""
Storage Package - Cloudflare R2 Integration

This package provides industrial-grade object storage for Catachess.
It is designed to be business-agnostic and highly maintainable.

Architecture:
- storage/core: Infrastructure layer (R2 client, config, errors)
- storage/game_history: Game history content domain (PGN storage)

Key Principles:
1. Separation of concerns: Infrastructure vs. content vs. index
2. Single responsibility: Each module has one clear purpose
3. No business logic in storage layer
4. Centralized key management
5. Protocol-based interfaces for future flexibility
"""
