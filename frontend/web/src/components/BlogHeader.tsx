/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * BlogHeader component - Category display, article title, history, and search.
 */

import React from "react";
import { ArrowLeftIcon, Cross2Icon } from "@radix-ui/react-icons";
import RecentArticlesHistory from "./RecentArticlesHistory";

type ViewMode = 'articles' | 'drafts' | 'my-published';

interface BlogHeaderProps {
  activeCategory?: string;
  searchQuery?: string;
  onSearchChange: (search: string) => void;
  viewMode?: ViewMode;
  isDetailView?: boolean;
  onBackClick?: () => void;
  articleTitle?: string;
  articleLoading?: boolean;
}

const CATEGORY_LABELS: { [key: string]: string } = {
  'pinned': 'Pinned Articles',
  'about': 'Our Stories',
  'function': 'Functions Intro',
  'user': 'Community',
  'official': 'Chessortag Official',
};

const VIEW_MODE_LABELS: { [key in ViewMode]: string } = {
  'articles': '',
  'drafts': 'Draft Box',
  'my-published': 'My Published Blogs',
};

const BlogHeader: React.FC<BlogHeaderProps> = ({
  activeCategory,
  searchQuery = "",
  onSearchChange,
  viewMode = 'articles',
  isDetailView = false,
  onBackClick,
  articleTitle,
  articleLoading = false,
}) => {
  const [localSearchQuery, setLocalSearchQuery] = React.useState(searchQuery);

  // Sync with external search query
  React.useEffect(() => {
    setLocalSearchQuery(searchQuery);
  }, [searchQuery]);

  // Debounced search
  React.useEffect(() => {
    if (!isDetailView) {
      const timeoutId = setTimeout(() => {
        onSearchChange(localSearchQuery);
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  }, [localSearchQuery, onSearchChange, isDetailView]);

  const handleSearchClear = () => {
    setLocalSearchQuery("");
  };

  // Determine label based on viewMode first, then category
  const getLabel = () => {
    // In detail view, show article title or loading state
    if (isDetailView) {
      if (articleLoading) {
        return 'Loading...';
      }
      return articleTitle || 'Article';
    }

    if (viewMode !== 'articles' && VIEW_MODE_LABELS[viewMode]) {
      return VIEW_MODE_LABELS[viewMode];
    }
    if (activeCategory) {
      return CATEGORY_LABELS[activeCategory] || activeCategory;
    }
    // When no category selected, show Chessortag Official (all official blogs)
    return 'Chessortag Official';
  };

  const categoryLabel = getLabel();

  return (
    <div className="blog-header">
      <div className="blog-header__title-wrap">
        <span className="blog-header__eyebrow">CataChess Journal</span>
        <h1 className="blog-header__title">
          {categoryLabel}
        </h1>
      </div>

      <div className="blog-header__actions">
        <RecentArticlesHistory />

        {isDetailView ? (
          <button
            type="button"
            onClick={onBackClick}
            className="blog-header__back"
          >
            <ArrowLeftIcon width={16} height={16} />
            <span>Back to blogs</span>
          </button>
        ) : (
        <div className="blog-header__search">
          <input
            type="text"
            placeholder="Search articles..."
            value={localSearchQuery}
            onChange={(e) => setLocalSearchQuery(e.target.value)}
            className="blog-header__search-input"
          />
          {localSearchQuery && (
            <button
              type="button"
              onClick={handleSearchClear}
              className="blog-header__search-clear"
              aria-label="Clear search"
            >
              <Cross2Icon width={13} height={13} />
            </button>
          )}
        </div>
        )}
      </div>
    </div>
  );
};

export default BlogHeader;
