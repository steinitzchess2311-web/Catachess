"""Search service for content and metadata search."""
from dataclasses import dataclass

from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.db.tables.search_index import SearchIndex
from workspace.domain.policies.permissions import can_read


@dataclass
class SearchResult:
    """Search result entry."""

    target_id: str
    target_type: str
    content: str
    author_id: str | None
    score: float | None = None
    highlight: str | None = None


@dataclass
class SearchResults:
    """Search results with pagination."""

    results: list[SearchResult]
    total: int
    page: int
    page_size: int
    has_more: bool


class SearchService:
    """Service for searching content and metadata."""

    def __init__(
        self,
        search_repo: SearchIndexRepository,
        node_repo: NodeRepository,
        acl_repo: ACLRepository,
    ) -> None:
        self.search_repo = search_repo
        self.node_repo = node_repo
        self.acl_repo = acl_repo

    async def search(
        self,
        query: str,
        user_id: str,
        target_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResults:
        """
        Search content with permission filtering.

        Args:
            query: Search query string
            user_id: Current user ID (for permission filtering)
            target_type: Optional filter by target type
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            SearchResults with filtered results
        """
        # Calculate offset
        offset = (page - 1) * page_size

        fetch_limit = page_size * 3

        index_results = await self.search_repo.search(
            query=query,
            target_type=target_type,
            limit=fetch_limit,
            offset=offset,
        )

        filtered_results: list[SearchResult] = []
        for entry in index_results:
            # Check if user has permission to see this result
            if await self._can_user_see_result(user_id, entry):
                filtered_results.append(
                    SearchResult(
                        target_id=entry.target_id,
                        target_type=entry.target_type,
                        content=entry.content,
                        author_id=entry.author_id,
                        highlight=self._extract_highlight(entry.content, query),
                    )
                )

                # Stop once we have enough results
                if len(filtered_results) >= page_size:
                    break

        # Include metadata matches for nodes in "all" searches.
        if target_type in (None, "workspace", "folder", "study"):
            metadata = await self.search_metadata(
                query=query,
                user_id=user_id,
                node_type=target_type,
                page=1,
                page_size=page_size,
            )
            existing = {(r.target_id, r.target_type) for r in filtered_results}
            for result in metadata.results:
                key = (result.target_id, result.target_type)
                if key in existing:
                    continue
                filtered_results.append(result)
                if len(filtered_results) >= page_size:
                    break

        # Determine if there are more results
        has_more = len(index_results) == fetch_limit

        return SearchResults(
            results=filtered_results[:page_size],
            total=len(filtered_results),  # Approximate, filtered total
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def search_metadata(
        self,
        query: str,
        user_id: str,
        node_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResults:
        """
        Search node metadata (workspace/folder/study names).

        Args:
            query: Search query
            user_id: Current user ID
            node_type: Optional filter by node type
            page: Page number
            page_size: Results per page

        Returns:
            SearchResults with matching nodes
        """
        # Search nodes by name
        nodes = await self.node_repo.search_by_name(
            query=query,
            node_type=node_type,
            limit=page_size * 3,  # Fetch extra for filtering
        )

        # Filter by permissions
        filtered_results = []
        for node in nodes:
            if await can_read(self.acl_repo, node, user_id):
                filtered_results.append(
                    SearchResult(
                        target_id=node.id,
                        target_type=node.node_type,
                        content=node.title,
                        author_id=node.owner_id,
                        highlight=node.title,
                    )
                )

                if len(filtered_results) >= page_size:
                    break

        return SearchResults(
            results=filtered_results[:page_size],
            total=len(filtered_results),
            page=page,
            page_size=page_size,
            has_more=len(nodes) == page_size * 3,
        )

    async def search_content(
        self,
        query: str,
        user_id: str,
        target_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResults:
        """
        Search full-text indexed content (discussions, annotations).

        This is an alias for the main search method.

        Args:
            query: Search query
            user_id: Current user ID
            target_type: Optional filter by target type
            page: Page number
            page_size: Results per page

        Returns:
            SearchResults with matching content
        """
        return await self.search(query, user_id, target_type, page, page_size)

    async def _can_user_see_result(
        self, user_id: str, entry: SearchIndex
    ) -> bool:
        """
        Check if user has permission to see this search result.

        SECURITY FIX: Changed default behavior to be more restrictive.
        Previously, this method returned True for most cases, allowing
        unauthorized access to search results.

        Args:
            user_id: User ID
            entry: Search index entry

        Returns:
            True if user can see this result
        """
        # For nodes (workspace/folder/study), check ACL
        if entry.target_type in ["workspace", "folder", "study"]:
            node = await self.node_repo.get_by_id(entry.target_id)
            return await can_read(self.acl_repo, node, user_id)

        # SECURITY FIX: For discussion threads and replies, we need proper permission checking
        # These need to resolve their parent object (study/chapter) and check ACL
        if entry.target_type in ["discussion_thread", "discussion_reply"]:
            # TODO: Implement proper permission check by:
            # 1. Looking up the thread's target_id and target_type from discussion_threads table
            # 2. If target is a study/chapter, check read permission on that resource
            # 3. If target is a reply, recursively find the root thread
            #
            # For now, SECURITY FIX: Return False to prevent leaking unauthorized content
            # This is safer than returning True, but will hide valid results
            # Needs proper implementation before enabling
            return False

        # SECURITY FIX: For chapters and annotations, check parent study permission
        if entry.target_type in ["chapter", "move_annotation"]:
            # TODO: Implement proper permission check by:
            # 1. Resolving the parent study ID from chapters table
            # 2. Checking read permission on the parent study
            #
            # For now, SECURITY FIX: Return False to prevent leaking unauthorized content
            return False

        # SECURITY FIX: Changed default from True to False
        # Better to hide results than leak unauthorized content
        # Unknown types should be explicitly handled above
        return False

    def _extract_highlight(self, content: str, query: str, context_size: int = 100) -> str:
        """
        Extract a highlighted snippet from content.

        Args:
            content: Full content text
            query: Search query
            context_size: Characters of context on each side

        Returns:
            Highlighted snippet
        """
        # Simple case-insensitive search
        query_lower = query.lower()
        content_lower = content.lower()

        # Find first occurrence
        pos = content_lower.find(query_lower)
        if pos == -1:
            # No exact match, return beginning
            return content[:context_size * 2] + ("..." if len(content) > context_size * 2 else "")

        # Extract context around match
        start = max(0, pos - context_size)
        end = min(len(content), pos + len(query) + context_size)

        snippet = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def build_search_query(
        self,
        query: str,
        filters: dict | None = None,
    ) -> str:
        """
        Build a search query with filters.

        Args:
            query: Base search query
            filters: Optional filters (target_type, author_id, etc.)

        Returns:
            Formatted search query
        """
        # For PostgreSQL full-text search, this would build a tsquery
        # For now, return the raw query
        return query
