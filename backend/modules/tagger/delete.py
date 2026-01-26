"""
Tagger delete helpers.

This module centralizes delete logic for tagger player data.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from models.tagger import PlayerProfile, PgnUpload, PgnGame, FailedGame, TagStat
from modules.tagger.storage import TaggerStorage, TaggerKeyBuilder


def _is_safe_upload_key(player_id: uuid.UUID, upload_id: uuid.UUID, key: str) -> bool:
    prefix = f"{TaggerKeyBuilder.PREFIX}/{player_id}/{upload_id}/"
    return key.startswith(prefix)


def delete_player_records(db: Session, player_id: uuid.UUID, storage: Optional[TaggerStorage] = None) -> bool:
    """
    Delete a player and all related tagger records from the database,
    and remove corresponding objects from R2.
    Returns True if the player existed and was deleted.
    """
    player = db.get(PlayerProfile, player_id)
    if not player:
        return False

    # Delete R2 objects for all uploads (raw.pgn + meta.json).
    tagger_storage = storage or TaggerStorage()
    uploads = list(db.query(PgnUpload).filter(PgnUpload.player_id == player_id).all())
    for upload in uploads:
        raw_key = TaggerKeyBuilder.raw_pgn(player_id, upload.id)
        meta_key = TaggerKeyBuilder.meta_json(player_id, upload.id)
        if _is_safe_upload_key(player_id, upload.id, raw_key):
            tagger_storage.delete_key(raw_key)
        if _is_safe_upload_key(player_id, upload.id, meta_key):
            tagger_storage.delete_key(meta_key)
        # If stored key is present and safely scoped, delete it too (covers legacy keys).
        if upload.r2_key_raw and _is_safe_upload_key(player_id, upload.id, upload.r2_key_raw):
            tagger_storage.delete_key(upload.r2_key_raw)

    db.query(FailedGame).filter(FailedGame.player_id == player_id).delete(synchronize_session=False)
    db.query(PgnGame).filter(PgnGame.player_id == player_id).delete(synchronize_session=False)
    db.query(PgnUpload).filter(PgnUpload.player_id == player_id).delete(synchronize_session=False)
    db.query(TagStat).filter(TagStat.player_id == player_id).delete(synchronize_session=False)
    db.delete(player)
    db.commit()
    return True
