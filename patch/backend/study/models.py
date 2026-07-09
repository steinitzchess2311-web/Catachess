"""
Created at: 2026-07-09 01:20 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:20 EDT
Last Modified by: Codex

Pydantic DTOs for persisted study tree JSON and patch study API responses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class StudyNodeDTO(BaseModel):
    id: str
    parentId: Optional[str] = None
    san: str
    children: List[str] = []
    comment: Optional[str] = None
    nags: List[int] = []
    # v2 optional fields – shapes (circles/arrows) and clock (centiseconds)
    shapes: Optional[List[Dict[str, Any]]] = None
    clock: Optional[int] = None
    is_base: Optional[bool] = None

    model_config = {
        "extra": "forbid"
    }

class TreeMetaDTO(BaseModel):
    result: Optional[str] = None

    model_config = {
        "extra": "forbid"
    }

class StudyTreeDTO(BaseModel):
    version: str
    rootId: str
    nodes: Dict[str, StudyNodeDTO]
    meta: TreeMetaDTO

    model_config = {
        "extra": "forbid"
    }

class TreeResponse(BaseModel):
    success: bool
    tree: Optional[StudyTreeDTO] = None
    starting_fen: Optional[str] = None  # Custom starting position (NULL = standard)
    tree_revision: int = 0
    tree_updated_at: Optional[str] = None
    error: Optional[str] = None
