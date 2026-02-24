/**
 * ArticleDetailPage component - Full blog article view
 * Displays complete article with Markdown rendering
 */

import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EyeOpenIcon, ChatBubbleIcon } from "@radix-ui/react-icons";
import { HandIcon } from "@radix-ui/react-icons";
import { useBlogArticle } from "../../hooks/useBlogArticle";
import { BlogArticle } from "../../types/blog";
import MarkdownRenderer from "./components/MarkdownRenderer";
import LoadingState from "./components/LoadingState";
import ErrorState from "./components/ErrorState";
import PageTransition from "../../components/animation/PageTransition";

interface ArticleDetailPageProps {
  embedded?: boolean;  // If true, render without PageTransition wrapper and back button
  article?: BlogArticle | null;  // Pre-fetched article data (for embedded mode)
  loading?: boolean;  // Pre-fetched loading state (for embedded mode)
}

/**
 * Full article detail page with back navigation
 * Automatically increments view count on load
 * Can be embedded in BlogsPage or used as standalone page
 */
const ArticleDetailPage: React.FC<ArticleDetailPageProps> = ({
  embedded = false,
  article: propArticle,
  loading: propLoading,
}) => {
  const { articleId } = useParams<{ articleId: string }>();
  const navigate = useNavigate();

  // Use prop data if provided (embedded mode), otherwise fetch with hook (standalone mode)
  const hookResult = useBlogArticle(propArticle !== undefined ? undefined : articleId);
  const article = propArticle !== undefined ? propArticle : hookResult.article;
  const loading = propLoading !== undefined ? propLoading : hookResult.loading;
  const error = propArticle !== undefined ? null : hookResult.error;

  const [isLiked, setIsLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);

  // Initialize like count when article loads
  React.useEffect(() => {
    if (article) {
      setLikeCount(article.like_count || 0);
    }
  }, [article]);

  // Handle like toggle
  const handleLikeToggle = () => {
    setIsLiked(!isLiked);
    setLikeCount(prev => isLiked ? prev - 1 : prev + 1);
    // TODO: Call API to update like count
  };

  // Loading state
  if (loading) {
    const loadingContent = <LoadingState />;

    if (embedded) {
      return (
        <div style={{
          background: "rgba(255, 255, 255, 0.85)",
          borderRadius: "12px",
          padding: "40px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
          minHeight: "400px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          {loadingContent}
        </div>
      );
    }

    return (
      <PageTransition>
        <div
          style={{
            minHeight: "100vh",
            background: "linear-gradient(135deg, #f8f4f0 0%, #e8ddd0 100%)",
            padding: "80px 24px 40px",
          }}
        >
          {loadingContent}
        </div>
      </PageTransition>
    );
  }

  // Error state
  if (error) {
    const errorContent = <ErrorState message="Failed to load article" />;

    if (embedded) {
      return (
        <div style={{
          background: "rgba(255, 255, 255, 0.85)",
          borderRadius: "12px",
          padding: "40px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
        }}>
          {errorContent}
        </div>
      );
    }

    return (
      <PageTransition>
        <div
          style={{
            minHeight: "100vh",
            background: "linear-gradient(135deg, #f8f4f0 0%, #e8ddd0 100%)",
            padding: "80px 24px 40px",
          }}
        >
          <div style={{ maxWidth: "800px", margin: "0 auto" }}>
            <button
              onClick={() => navigate("/blogs")}
              style={{
                padding: "10px 20px",
                marginBottom: "20px",
                fontSize: "0.95rem",
                fontWeight: 500,
                color: "#0f172a",
                backgroundColor: "rgba(255, 255, 255, 0.9)",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(37, 99, 235, 0.1)";
                e.currentTarget.style.borderColor = "#2563eb";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.9)";
                e.currentTarget.style.borderColor = "#e2e8f0";
              }}
            >
              ← Back to Blogs
            </button>
            {errorContent}
          </div>
        </div>
      </PageTransition>
    );
  }

  // Not found state
  if (!article) {
    const notFoundContent = (
      <div
        style={{
          textAlign: "center",
          padding: "60px 20px",
        }}
      >
        <h1 style={{ fontSize: "3rem", marginBottom: "20px" }}>404</h1>
        <p style={{ fontSize: "1.2rem", color: "#475569", marginBottom: "30px" }}>
          Article not found
        </p>
        {!embedded && (
          <button
            onClick={() => navigate("/blogs")}
            style={{
              padding: "12px 30px",
              fontSize: "1rem",
              fontWeight: 600,
              color: "white",
              backgroundColor: "#2563eb",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#1d4ed8";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "#2563eb";
            }}
          >
            Back to Blogs
          </button>
        )}
      </div>
    );

    if (embedded) {
      return (
        <div style={{
          background: "rgba(255, 255, 255, 0.85)",
          borderRadius: "12px",
          padding: "40px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
        }}>
          {notFoundContent}
        </div>
      );
    }

    return (
      <PageTransition>
        <div
          style={{
            minHeight: "100vh",
            background: "linear-gradient(135deg, #f8f4f0 0%, #e8ddd0 100%)",
            padding: "80px 24px 40px",
          }}
        >
          <div style={{ maxWidth: "800px", margin: "0 auto" }}>
            {notFoundContent}
          </div>
        </div>
      </PageTransition>
    );
  }

  // Format date
  const formattedDate = new Date(article.published_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  // Article content (reusable for both embedded and standalone modes)
  const articleContent = (
    <article
      style={{
        background: "rgba(255, 255, 255, 0.95)",
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
      }}
    >
            {/* Cover Image */}
            <div
              style={{
                width: "100%",
                height: "400px",
                overflow: "hidden",
                backgroundColor: "#f5f5f5",
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

            {/* Article Content */}
            <div style={{ padding: "40px" }}>
              {/* Title */}
              <h1
                style={{
                  fontSize: "2.5rem",
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
                  fontSize: "1.3rem",
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
                        ? "rgba(76, 175, 80, 0.1)"  // 绿色 - 官方文章
                        : "rgba(37, 99, 235, 0.1)",  // 棕色 - 用户投稿
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}
                  >
                    {article.author_type === 'official' ? 'Official' : 'User'}
                  </span>
                </div>
                <span style={{ color: "#d0d0d0" }}>•</span>
                <span>{formattedDate}</span>
                <span style={{ color: "#d0d0d0" }}>•</span>
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
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    color: isLiked ? "#2563eb" : "#64748b",
                    border: "none",
                    background: "transparent",
                    cursor: "pointer",
                    fontSize: "0.95rem",
                    padding: "4px 8px",
                    borderRadius: "6px",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (!isLiked) {
                      e.currentTarget.style.color = "#2563eb";
                      e.currentTarget.style.backgroundColor = "rgba(37, 99, 235, 0.08)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isLiked) {
                      e.currentTarget.style.color = "#64748b";
                      e.currentTarget.style.backgroundColor = "transparent";
                    }
                  }}
                >
                  <HandIcon
                    width={18}
                    height={18}
                    style={{
                      fill: isLiked ? "#2563eb" : "none",
                      transform: "rotate(0deg)"
                    }}
                  />
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
          </article>
  );

  // Embedded mode: render article within BlogsPage container
  if (embedded) {
    return articleContent;
  }

  // Standalone mode: render with PageTransition and back button
  return (
    <PageTransition>
      <div
        style={{
          minHeight: "100vh",
          background: "linear-gradient(135deg, #f8f4f0 0%, #e8ddd0 100%)",
          padding: "80px 24px 40px",
          overflowY: "auto",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          {/* Back Button */}
          <button
            onClick={() => navigate("/blogs")}
            style={{
              padding: "10px 20px",
              marginBottom: "30px",
              fontSize: "0.95rem",
              fontWeight: 500,
              color: "#0f172a",
              backgroundColor: "rgba(255, 255, 255, 0.9)",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(37, 99, 235, 0.1)";
              e.currentTarget.style.borderColor = "#2563eb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.9)";
              e.currentTarget.style.borderColor = "#e2e8f0";
            }}
          >
            ← Back to Blogs
          </button>

          {articleContent}
        </div>
      </div>
    </PageTransition>
  );
};

export default ArticleDetailPage;
