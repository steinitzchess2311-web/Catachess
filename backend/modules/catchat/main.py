"""
=============================================================
  CATCHAT DATABASE INITIALISATION  (called at app startup)
=============================================================
Purpose : Create all catchat tables in CATCHAT_DATABASE.
Deploy  : backend/main.py calls init_catchat_db() in its lifespan.
          Railway auto-deploys on push → tables are created on first boot.
Cleanup : All statements use IF NOT EXISTS — safe to run every startup.
          You may remove this file after confirming tables exist, but
          keeping it is harmless and protects against accidental drops.
=============================================================
"""
import os
import logging

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# ── DDL ────────────────────────────────────────────────────────────────────────

_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS catchat_conversations (
    id              UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    user1_id        UUID      NOT NULL,           -- always the smaller UUID of the pair
    user2_id        UUID      NOT NULL,           -- always the larger UUID of the pair
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW(), -- updated on every new message
    CONSTRAINT uq_catchat_conv_pair UNIQUE (user1_id, user2_id)
);
CREATE INDEX IF NOT EXISTS ix_catchat_conv_user1 ON catchat_conversations(user1_id);
CREATE INDEX IF NOT EXISTS ix_catchat_conv_user2 ON catchat_conversations(user2_id);
CREATE INDEX IF NOT EXISTS ix_catchat_conv_last  ON catchat_conversations(last_message_at DESC);
"""

_MESSAGES = """
CREATE TABLE IF NOT EXISTS catchat_messages (
    id              UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID      NOT NULL,           -- FK → catchat_conversations.id
    sender_id       UUID      NOT NULL,           -- user who sent this
    sender_name     VARCHAR(50),                  -- denormalised username at send time
    content         TEXT      NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_catchat_msg_conv ON catchat_messages(conversation_id, created_at DESC);
"""

_BROADCASTS = """
CREATE TABLE IF NOT EXISTS catchat_broadcasts (
    id          UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id   UUID      NOT NULL,               -- admin user ID
    sender_name VARCHAR(50) NOT NULL,             -- denormalised username
    content     TEXT      NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_catchat_bcast_created ON catchat_broadcasts(created_at DESC);
"""

# ── Entry point ────────────────────────────────────────────────────────────────

def init_catchat_db() -> None:
    """Create catchat tables if they don't exist. Safe to call on every startup."""
    url = os.getenv("CATCHAT_DATABASE")
    if not url:
        logger.warning("CATCHAT_DATABASE not set — skipping catchat DB init")
        return

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(_CONVERSATIONS))
        conn.execute(text(_MESSAGES))
        conn.execute(text(_BROADCASTS))
    logger.info("✅ catchat tables ready")
