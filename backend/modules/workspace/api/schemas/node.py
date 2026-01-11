"""
Node API schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workspace.domain.models.types import NodeType, Visibility


class NodeCreate(BaseModel):
    """Schema for creating a node."""

    node_type: NodeType
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    parent_id: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    layout: dict[str, Any] = Field(default_factory=dict)


class NodeUpdate(BaseModel):
    """Schema for updating a node."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    visibility: Visibility | None = None
    layout: dict[str, Any] | None = None
    version: int | None = None


class NodeMove(BaseModel):
    """Schema for moving a node."""

    new_parent_id: str | None
    version: int


class NodeResponse(BaseModel):
    """Schema for node response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    node_type: NodeType
    title: str
    description: str | None
    owner_id: str
    visibility: Visibility
    parent_id: str | None
    path: str
    depth: int
    layout: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class NodeListResponse(BaseModel):
    """Schema for list of nodes."""

    nodes: list[NodeResponse]
    total: int
