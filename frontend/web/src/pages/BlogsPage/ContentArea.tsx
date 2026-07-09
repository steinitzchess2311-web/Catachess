/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ContentArea component - blog article list/detail display.
 */

import React, { useState, useEffect } from "react";
import { useBlogArticles } from "../../hooks/useBlogArticles";
import { blogApi } from "../../utils/blogApi";
import { BlogArticle } from "../../types/blog";
import ArticleCard from "./ArticleCard";
import LoadingState from "./components/LoadingState";
import EmptyState from "./components/EmptyState";
import ErrorState from "./components/ErrorState";
import Pagination from "./components/Pagination";
import ArticleDetailContent from "./ArticleDetailContent";

type ViewMode = 'articles' | 'drafts' | 'my-published';

interface ContentAreaProps {
  category?: string;  // Category filter (about, function, allblogs) - for API calls
  search?: string;    // Search query
  page?: number;      // Current page number
  onPageChange: (page: number) => void;  // Callback for page changes
  userRole?: string | null;  // User's role for showing create button
  viewMode: ViewMode;  // View mode: articles, drafts, or my-published
  isDetailView?: boolean;  // Whether showing article detail
  articleId?: string;  // Article ID when in detail view
  article?: BlogArticle | null;  // Pre-fetched article data
  articleLoading?: boolean;  // Article loading state
  categoryParam?: string;  // Original category from URL (for history tracking)
  sidebarOpen?: boolean; // Whether category sidebar is expanded
}

/**
 * Main content area that displays blog articles in a grid
 * Handles all data fetching and state management
 * Supports three view modes: articles (paginated), drafts (user's drafts), my-published (user's published)
 */
const ContentArea: React.FC<ContentAreaProps> = ({
  category,
  search,
  page = 1,
  onPageChange,
  userRole,
  viewMode,
  isDetailView = false,
  articleId,
  article,
  articleLoading = false,
  categoryParam,
  sidebarOpen = true,
}) => {
  // State for drafts and my-published views
  const [myArticles, setMyArticles] = useState<BlogArticle[]>([]);
  const [myLoading, setMyLoading] = useState(false);
  const [myError, setMyError] = useState<Error | null>(null);

  // Fetch articles with current filters (for 'articles' view mode)
  const { articles, loading, error, pagination } = useBlogArticles({
    category,
    search,
    page,
    page_size: 10,
  });

  // Fetch drafts, my-published, or pinned articles when view mode or category changes
  useEffect(() => {
    const fetchMyArticles = async () => {
      // Skip for normal articles view (unless it's pinned category)
      if (viewMode === 'articles' && category !== 'pinned') return;

      setMyLoading(true);
      setMyError(null);

      try {
        let data: BlogArticle[];
        if (viewMode === 'drafts') {
          data = await blogApi.getMyDrafts();
        } else if (viewMode === 'my-published') {
          data = await blogApi.getMyPublished();
        } else if (category === 'pinned') {
          // Handle pinned articles
          data = await blogApi.getPinnedArticles();
        } else {
          return; // Should not reach here
        }
        setMyArticles(data);
      } catch (err) {
        setMyError(err instanceof Error ? err : new Error('Failed to fetch articles'));
      } finally {
        setMyLoading(false);
      }
    };

    fetchMyArticles();
  }, [viewMode, category]);

  // Handle article deletion
  const handleDelete = (articleId: string) => {
    if (viewMode === 'articles') {
      // Refresh articles view - this will be handled by useBlogArticles hook automatically
      // Or we can trigger a manual refetch here
      window.location.reload(); // Simple approach for now
    } else {
      // Remove from local state for drafts/my-published views
      setMyArticles(prev => prev.filter(article => article.id !== articleId));
    }
  };

  // Handle category change
  const handleCategoryChange = (articleId: string, newCategory: string) => {
    setMyArticles(prev =>
      prev.map(article =>
        article.id === articleId ? { ...article, category: newCategory } : article
      )
    );
  };

  // Handle pin toggle
  const handlePinToggle = (articleId: string) => {
    // Refresh to get updated pin status
    if (viewMode === 'articles') {
      window.location.reload(); // Simple approach for now
    } else {
      // For drafts/my-published, update local state
      setMyArticles(prev =>
        prev.map(article =>
          article.id === articleId
            ? { ...article, is_pinned: !article.is_pinned }
            : article
        )
      );
    }
  };

  // Determine which data to display based on view mode and category
  const displayArticles = (viewMode === 'articles' && category !== 'pinned') ? articles : myArticles;
  const displayLoading = (viewMode === 'articles' && category !== 'pinned') ? loading : myLoading;
  const displayError = (viewMode === 'articles' && category !== 'pinned') ? error : myError;

  return (
    <div
      className={`blogs-content-surface${isDetailView ? ' is-detail' : ''}`}
    >
      {/* Article Detail View */}
      {isDetailView ? (
        <ArticleDetailContent
          article={article}
          loading={articleLoading}
          articleId={articleId}
          currentCategory={categoryParam}
        />
      ) : (
        <>
          {/* Loading State */}
          {displayLoading && <LoadingState />}

          {/* Error State */}
          {!displayLoading && displayError && <ErrorState message={displayError.message} />}

          {/* Empty State */}
          {!displayLoading && !displayError && displayArticles.length === 0 && <EmptyState />}

          {/* Articles Grid */}
          {!displayLoading && !displayError && displayArticles.length > 0 && (
            <>
              <div
                className="blogs-grid"
                data-sidebar-open={sidebarOpen}
              >
                {displayArticles.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    userRole={userRole}
                    viewMode={viewMode}
                    onDelete={handleDelete}
                    onPinToggle={handlePinToggle}
                    onCategoryChange={handleCategoryChange}
                  />
                ))}
              </div>

              {/* Pagination Controls - Only for 'articles' view and not pinned */}
              {viewMode === 'articles' && category !== 'pinned' && pagination.total_pages > 1 && (
                <Pagination pagination={pagination} onPageChange={onPageChange} />
              )}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default ContentArea;
