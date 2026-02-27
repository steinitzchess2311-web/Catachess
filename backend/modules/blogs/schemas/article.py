"""
Article Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


# ==================== Category Schemas ====================

class CategoryResponse(BaseModel):
    """Category response schema"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Article Schemas ====================

class ArticleBase(BaseModel):
    """Base article schema"""
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = None
    content: str = Field(..., min_length=1)
    cover_image_url: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None


class ArticleCreate(ArticleBase):
    """Create article request"""
    author_name: str = Field(default="Chessortag Team", max_length=100)
    author_type: str = Field(default="official", pattern="^(official|user)$")
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    is_pinned: bool = False
    pin_order: int = 0


class ArticleUpdate(BaseModel):
    """Update article request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    cover_image_url: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    is_pinned: Optional[bool] = None
    pin_order: Optional[int] = None


class ArticleResponse(BaseModel):
    """Article response schema"""
    id: UUID
    title: str
    subtitle: Optional[str]
    content: str
    cover_image_url: Optional[str]

    author_id: Optional[UUID]
    author_name: str
    author_type: str

    category: str
    sub_category: Optional[str]
    tags: Optional[List[str]]

    status: str
    is_pinned: bool
    pin_order: int

    view_count: int
    like_count: int
    comment_count: int
    is_liked: bool = False  # Whether the current user has liked this article

    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class ArticleListItem(BaseModel):
    """Article list item (summary)"""
    id: UUID
    title: str
    subtitle: Optional[str]
    cover_image_url: Optional[str]

    author_name: str
    author_type: str

    category: str
    tags: Optional[List[str]]

    is_pinned: bool

    view_count: int
    like_count: int
    comment_count: int

    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Article list response with pagination"""
    items: List[ArticleListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
