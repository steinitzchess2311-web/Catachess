/**
 * ArticleDetailContent - Pure content component for article details
 * Displays article cover, title, metadata, content, and stats
 * Designed to be rendered within ContentArea container
 */

import React, { useState } from "react";
import { EyeOpenIcon, ChatBubbleIcon, HeartIcon, HeartFilledIcon } from "@radix-ui/react-icons";
import { BlogArticle } from "../../types/blog";
import MarkdownRenderer from "./components/MarkdownRenderer";
import LoadingState from "./components/LoadingState";
import ErrorState from "./components/ErrorState";
import { useBlogArticle } from "../../hooks/useBlogArticle";
import { saveCategoryLastArticle, addRecentArticle } from "../../utils/articleHistory";
import { blogApi } from "../../utils/blogApi";

interface ArticleDetailContentProps {
  article?: BlogArticle | null;
  loading?: boolean;
  articleId?: string;
  currentCategory?: string; // Current category from URL for history tracking
}

const ArticleDetailContent: React.FC<ArticleDetailContentProps> = ({
  article: propArticle,
  loading: propLoading,
  articleId,
  currentCategory,
}) => {
  // Fallback: fetch article if not provided
  const hookResult = useBlogArticle(propArticle !== undefined ? undefined : articleId);
  const article = propArticle !== undefined ? propArticle : hookResult.article;
  const loading = propLoading !== undefined ? propLoading : hookResult.loading;
  const error = propArticle !== undefined ? null : hookResult.error;

  const [isLiked, setIsLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [liking, setLiking] = useState(false);

  // Sync like state from article data (including is_liked from backend)
  React.useEffect(() => {
    if (article) {
      setLikeCount(article.like_count || 0);
      setIsLiked(article.is_liked ?? false);
    }
  }, [article]);

  // Save article to history when loaded
  React.useEffect(() => {
    if (article) {
      // Save to category last article (for "return to this article" feature)
      saveCategoryLastArticle(currentCategory, article.id);

      // Save to recent articles (for history list - will implement UI later)
      addRecentArticle({
        id: article.id,
        title: article.title,
        category: currentCategory,
      });
    }
  }, [article, currentCategory]);

  // Handle like toggle — optimistic update, roll back on error
  const handleLikeToggle = async () => {
    if (!article || liking) return;

    // Optimistic update
    const nextLiked = !isLiked;
    setIsLiked(nextLiked);
    setLikeCount(prev => nextLiked ? prev + 1 : Math.max(prev - 1, 0));
    setLiking(true);

    try {
      const res = await blogApi.toggleLike(article.id);
      // Sync with server truth
      setIsLiked(res.liked);
      setLikeCount(res.like_count);
    } catch {
      // Roll back optimistic update on failure
      setIsLiked(isLiked);
      setLikeCount(prev => isLiked ? prev + 1 : Math.max(prev - 1, 0));
    } finally {
      setLiking(false);
    }
  };

  // Loading state
  if (loading) {
    return <LoadingState />;
  }

  // Error state
  if (error) {
    return <ErrorState message="Failed to load article" />;
  }

  // Not found state
  if (!article) {
    return (
      <div style={{ textAlign: "center", padding: "60px 20px" }}>
        <h1 style={{ fontSize: "3rem", marginBottom: "20px" }}>404</h1>
        <p style={{ fontSize: "1.2rem", color: "#475569" }}>Article not found</p>
      </div>
    );
  }

  // Format date
  const formattedDate = new Date(article.published_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto" }}>
      {/* Cover Image */}
      <div
        style={{
          width: "100%",
          height: "clamp(220px, 38vw, 400px)",
          overflow: "hidden",
          backgroundColor: "#f5f5f5",
          borderRadius: "8px",
          marginBottom: "32px",
        }}
      >
        <img
          src={article.cover_image_url}
          alt={article.title}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: "clamp(1.85rem, 3.4vw, 2.35rem)",
          fontWeight: 700,
          color: "#0f172a",
          marginBottom: "12px",
          lineHeight: "1.3",
        }}
      >
        {article.title}
      </h1>

      {/* Subtitle */}
      <h2
        style={{
          fontSize: "clamp(1rem, 2.2vw, 1.2rem)",
          fontWeight: 400,
          color: "#475569",
          marginBottom: "24px",
          lineHeight: "1.5",
        }}
      >
        {article.subtitle}
      </h2>

      {/* Metadata */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          paddingBottom: "24px",
          marginBottom: "32px",
          borderBottom: "2px solid rgba(37, 99, 235, 0.15)",
          fontSize: "0.95rem",
          color: "#2563eb",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontWeight: 600 }}>{article.author_name}</span>
          <span
            style={{
              padding: "4px 8px",
              backgroundColor: article.author_type === 'official'
                ? "rgba(76, 175, 80, 0.1)"
                : "rgba(37, 99, 235, 0.1)",
              borderRadius: "4px",
              fontSize: "0.75rem",
              fontWeight: 600,
              textTransform: "uppercase",
            }}
          >
            {article.author_type === 'official' ? 'Official' : 'User'}
          </span>
        </div>
        <span style={{ color: "#cbd5e1" }}>•</span>
        <span>{formattedDate}</span>
        <span style={{ color: "#cbd5e1" }}>•</span>
        <span>{article.view_count} views</span>
      </div>

      {/* Tags */}
      {article.tags && article.tags.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            marginBottom: "32px",
          }}
        >
          {article.tags.map((tag, index) => (
            <span
              key={index}
              style={{
                padding: "6px 14px",
                backgroundColor: "rgba(37, 99, 235, 0.1)",
                color: "#2563eb",
                borderRadius: "20px",
                fontSize: "0.85rem",
                fontWeight: 500,
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Article Content - Markdown */}
      {article.content && (
        <MarkdownRenderer content={article.content} />
      )}

      {/* Footer Stats */}
      <div
        style={{
          marginTop: "40px",
          paddingTop: "24px",
          borderTop: "1px solid rgba(37, 99, 235, 0.15)",
          display: "flex",
          gap: "32px",
          fontSize: "0.95rem",
          alignItems: "center",
        }}
      >
        {/* Views */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: "#64748b",
          }}
        >
          <EyeOpenIcon width={18} height={18} />
          <span>{article.view_count || 0}</span>
        </div>

        {/* Likes - Interactive */}
        <button
          onClick={handleLikeToggle}
          disabled={liking}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: isLiked ? "#e11d48" : "#64748b",
            border: "none",
            background: "transparent",
            cursor: liking ? "wait" : "pointer",
            fontSize: "0.95rem",
            padding: "4px 8px",
            borderRadius: "6px",
            transition: "all 0.2s ease",
            opacity: liking ? 0.6 : 1,
          }}
          onMouseEnter={(e) => {
            if (!isLiked) {
              e.currentTarget.style.color = "#e11d48";
              e.currentTarget.style.backgroundColor = "rgba(225, 29, 72, 0.08)";
            }
          }}
          onMouseLeave={(e) => {
            if (!isLiked) {
              e.currentTarget.style.color = "#64748b";
              e.currentTarget.style.backgroundColor = "transparent";
            }
          }}
        >
          {isLiked
            ? <HeartFilledIcon width={18} height={18} style={{ color: "#e11d48" }} />
            : <HeartIcon width={18} height={18} />
          }
          <span>{likeCount}</span>
        </button>

        {/* Comments */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: "#64748b",
          }}
        >
          <ChatBubbleIcon width={18} height={18} />
          <span>{article.comment_count || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default ArticleDetailContent;
