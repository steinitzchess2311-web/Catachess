/**
 * Created at: 2026-07-09 01:27 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:27 EDT
 * Last Modified by: Codex
 *
 * ArticleDetailContent - reading view for blog articles.
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
import { useUser } from "../../contexts/UserContext";
import CommentSection from "./Comments";

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

  const { userId, username, userRole } = useUser();

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
      <div className="blog-state">
        <p className="blog-state__title">Article not found</p>
      </div>
    );
  }

  // Format date
  const formattedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : null;

  return (
    <article className="blog-detail">
      {/* Cover Image */}
      <div className="blog-detail__cover">
        {article.cover_image_url ? (
          <img
            src={article.cover_image_url}
            alt={article.title}
            className="blog-detail__cover-image"
          />
        ) : (
          <div className="blog-detail__cover-placeholder">No cover</div>
        )}
      </div>

      {/* Title */}
      <h1 className="blog-detail__title">
        {article.title}
      </h1>

      {/* Subtitle */}
      {article.subtitle && (
        <p className="blog-detail__subtitle">
          {article.subtitle}
        </p>
      )}

      {/* Metadata */}
      <div className="blog-detail__meta">
        <div className="blog-detail__author">
          <span>{article.author_name}</span>
          <span className="blog-detail__badge">
            {article.author_type === 'official' ? 'Official' : 'User'}
          </span>
        </div>
        {formattedDate && (
          <>
            <span className="blog-detail__dot" />
            <span>{formattedDate}</span>
          </>
        )}
        <span className="blog-detail__dot" />
        <span>{article.view_count} views</span>
      </div>

      {/* Tags */}
      {article.tags && article.tags.length > 0 && (
        <div className="blog-detail__tags">
          {article.tags.map((tag, index) => (
            <span
              key={index}
              className="blog-detail__tag"
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
      <div className="blog-detail__stats">
        {/* Views */}
        <div className="blog-detail__stat">
          <EyeOpenIcon width={18} height={18} />
          <span>{article.view_count || 0}</span>
        </div>

        {/* Likes - Interactive */}
        <button
          onClick={handleLikeToggle}
          disabled={liking}
          className={`blog-detail__stat blog-detail__like${isLiked ? ' is-liked' : ''}`}
        >
          {isLiked
            ? <HeartFilledIcon width={18} height={18} />
            : <HeartIcon width={18} height={18} />
          }
          <span>{likeCount}</span>
        </button>

        {/* Comments */}
        <div className="blog-detail__stat">
          <ChatBubbleIcon width={18} height={18} />
          <span>{article.comment_count || 0}</span>
        </div>
      </div>

      {/* Comments */}
      <CommentSection
        articleId={article.id}
        currentUserId={userId ?? undefined}
        currentUserName={username ?? undefined}
        isAdmin={userRole === 'admin'}
      />
    </article>
  );
};

export default ArticleDetailContent;
