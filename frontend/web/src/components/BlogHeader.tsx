/**
 * BlogHeader component - Category display and search bar
 * Non-floating header for blog content area
 */

import React from "react";
import { ArrowLeftIcon } from "@radix-ui/react-icons";
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
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 22px",
        background: "#ffffff",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        marginBottom: "16px",
        boxShadow: "var(--shadow-1)",
      }}
    >
      {/* Left: Category Label or Article Title */}
      <div
        style={{
          fontSize: "1.35rem",
          fontWeight: 700,
          color: "var(--text-main)",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          maxWidth: "70%",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        <span style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}>
          {categoryLabel}
        </span>
      </div>

      {/* Right: History Icon + Search Bar or Back Button */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* Recent Articles History Icon */}
        <RecentArticlesHistory />

        {isDetailView ? (
          <button
            onClick={onBackClick}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 20px",
              border: "1px solid #bfdbfe",
              borderRadius: "8px",
              fontSize: "0.9rem",
              color: "var(--text-main)",
              backgroundColor: "#f8fbff",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#2563eb";
              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(37, 99, 235, 0.12)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#bfdbfe";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            <ArrowLeftIcon width={16} height={16} />
            <span>Back to Blogs</span>
          </button>
        ) : (
        <div
          style={{
            position: "relative",
            width: "320px",
          }}
        >
          <input
            type="text"
            placeholder="Search articles..."
            value={localSearchQuery}
            onChange={(e) => setLocalSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "10px 40px 10px 16px",
              border: "1px solid #bfdbfe",
              borderRadius: "8px",
              fontSize: "0.9rem",
              color: "var(--text-main)",
              backgroundColor: "#f8fbff",
              boxSizing: "border-box",
              transition: "all 0.2s ease",
              outline: "none",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "#2563eb";
              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(37, 99, 235, 0.12)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "#bfdbfe";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
          {localSearchQuery && (
            <button
              onClick={handleSearchClear}
              style={{
                position: "absolute",
                top: "50%",
                right: "12px",
                transform: "translateY(-50%)",
                width: "24px",
                height: "24px",
                border: "none",
                background: "rgba(37, 99, 235, 0.12)",
                borderRadius: "50%",
                fontSize: "16px",
                lineHeight: "1",
                color: "#475569",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "background 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(37, 99, 235, 0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(37, 99, 235, 0.12)";
              }}
            >
              ×
            </button>
          )}
        </div>
        )}
      </div>
    </div>
  );
};

export default BlogHeader;
