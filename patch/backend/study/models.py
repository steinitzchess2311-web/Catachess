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
    error: Optional[str] = None
