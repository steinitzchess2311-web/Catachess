"""Search API schemas."""
from pydantic import BaseModel, Field, model_serializer


class SearchResultItem(BaseModel):
    """Single search result item."""

    target_id: str = Field(..., description="Target object ID")
    target_type: str = Field(..., description="Target object type (study, discussion_thread, etc.)")
    content: str = Field(..., description="Content snippet")
    author_id: str | None = Field(None, description="Author user ID")
    highlight: str | None = Field(None, description="Highlighted snippet with context")
    score: float | None = Field(None, description="Relevance score")

    @model_serializer(mode="plain")
    def _serialize(self) -> dict:
        return {
            "id": self.target_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "content": self.content,
            "author_id": self.author_id,
            "highlight": self.highlight,
            "score": self.score,
        }


class SearchResponse(BaseModel):
    """Search results response."""

    results: list[SearchResultItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results (approximate)")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    has_more: bool = Field(..., description="Whether there are more results")
    query: str = Field(..., description="Original search query")


class SearchQuery(BaseModel):
    """Search query parameters."""

    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    target_type: str | None = Field(None, description="Filter by target type")
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Results per page")
    search_type: str = Field("all", description="Search type: all, metadata, content")


class MetadataSearchResponse(BaseModel):
    """Metadata search results (workspace/folder/study names)."""

    results: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    query: str


class ContentSearchResponse(BaseModel):
    """Content search results (discussions, annotations)."""

    results: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    query: str
