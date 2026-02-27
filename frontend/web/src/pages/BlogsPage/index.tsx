/**
 * BlogsPage - Main blog listing page
 * Manages URL-based state for category filtering, search, and pagination
 */

import { useSearchParams, useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import PageTransition from "../../components/animation/PageTransition";
import CategorySidebar from "./CategorySidebar";
import ContentArea from "./ContentArea";
import BlogHeader from "../../components/BlogHeader";
import ArticleDetailPage from "./ArticleDetailPage";
import { useBlogArticle } from "../../hooks/useBlogArticle";
import { getCategoryLastArticle, clearCategoryLastArticle } from "../../utils/articleHistory";
import { useUser } from "../../contexts/UserContext";
import "./BlogsPage.css";

/**
 * Main blog page with sidebar navigation and article grid
 * Uses URL search params for state management (category, search, page)
 */
type ViewMode = 'articles' | 'drafts' | 'my-published';

const BlogsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { articleId } = useParams<{ articleId: string }>();
  const navigate = useNavigate();
  const { userRole, username: userName } = useUser();
  const [viewMode, setViewMode] = useState<ViewMode>('articles');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  // Check if we're in detail view
  const isDetailView = Boolean(articleId);

  // Fetch article data when in detail view (for header title)
  const { article, loading: articleLoading } = useBlogArticle(
    isDetailView ? articleId : undefined
  );

  // Auto-collapse sidebar when entering detail view
  // Don't auto-expand when exiting detail view - preserve user's preference
  useEffect(() => {
    if (isDetailView) {
      setSidebarOpen(false);
    }
    // Removed: else { setSidebarOpen(true); }
    // User should manually control sidebar expansion
  }, [isDetailView]);

  // Extract current state from URL params
  // Default to 'pinned' category if no category specified
  const categoryParam = searchParams.get('category') || 'pinned';
  const search = searchParams.get('search') || undefined;
  const page = parseInt(searchParams.get('page') || '1', 10);

  // Pass categoryParam directly to API; backend handles 'official' → filter by author_type
  const category = categoryParam;


  /**
   * Handle category filter change
   * Implements "remember last article" feature:
   * - If user is viewing an article and clicks its category: exit to list (clear memory)
   * - If user clicks a different category: check if there's a remembered article
   * - If remembered article exists: navigate to that article
   * - Otherwise: navigate to list view
   */
  const handleCategoryChange = (newCategory: string | undefined) => {
    // Check if this is an "exit" action (clicking same category while viewing article)
    const isExitingCurrentArticle = isDetailView && categoryParam === newCategory;

    if (isExitingCurrentArticle) {
      // User wants to exit detail view - clear the memory for this category
      clearCategoryLastArticle(newCategory);
    }

    // Check if we should return to a remembered article
    const lastArticleId = getCategoryLastArticle(newCategory);

    if (!isExitingCurrentArticle && lastArticleId) {
      // Return to the last viewed article in this category
      navigate(`/blogs/${lastArticleId}`, { replace: isDetailView });
    } else {
      // Navigate to category list view
      const params = new URLSearchParams();

      if (newCategory) {
        params.set('category', newCategory);
      }

      if (search) {
        params.set('search', search);
      }

      params.set('page', '1');  // Reset to first page

      // Navigate to /blogs (without articleId in path)
      navigate(`/blogs?${params.toString()}`, { replace: isDetailView });
    }
  };

  /**
   * Handle search query change
   * Resets to page 1 when search changes
   * Clears articleId to return to list view
   */
  const handleSearchChange = (newSearch: string) => {
    // Navigate to /blogs with new search (clears articleId from URL)
    const params = new URLSearchParams();

    if (categoryParam) {
      params.set('category', categoryParam);
    }

    if (newSearch) {
      params.set('search', newSearch);
    }

    params.set('page', '1');  // Reset to first page

    // Navigate to /blogs (without articleId in path)
    navigate(`/blogs?${params.toString()}`);
  };

  /**
   * Handle page number change
   * Preserves current category and search filters
   */
  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', String(newPage));
    setSearchParams(params);
  };

  return (
    <PageTransition>
      <div className="blogs-page-shell">
        <div className="blogs-page-container">
          {/* Main Layout: Sidebar + Content */}
          <div
            className={`blogs-main-layout ${sidebarOpen ? "is-expanded" : "is-rail"}`}
          >
            <CategorySidebar
              activeCategory={categoryParam}
              searchQuery={search}
              onCategoryChange={handleCategoryChange}
              onSearchChange={handleSearchChange}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              userRole={userRole}
              userName={userName}
              isOpen={sidebarOpen}
              onOpenChange={setSidebarOpen}
            />

            {/* Content Column: Header + Content */}
            <div className="blogs-content-column">
              <BlogHeader
                activeCategory={categoryParam}
                searchQuery={search}
                onSearchChange={handleSearchChange}
                viewMode={viewMode}
                isDetailView={isDetailView}
                onBackClick={() => {
                  // Clear the category last article when clicking Back to Blogs
                  clearCategoryLastArticle(categoryParam);
                  navigate('/blogs');
                }}
                articleTitle={article?.title}
                articleLoading={articleLoading}
              />

              {/* ContentArea handles both list and detail views */}
              <ContentArea
                category={category}
                search={search}
                page={page}
                onPageChange={handlePageChange}
                userRole={userRole}
                viewMode={viewMode}
                isDetailView={isDetailView}
                articleId={articleId}
                article={article}
                articleLoading={articleLoading}
                categoryParam={categoryParam}
                sidebarOpen={sidebarOpen}
              />
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
};

export default BlogsPage;
