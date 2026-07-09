/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ArticleMeta component - author, date, and view count metadata.
 */

import React from "react";
import { ArticleMetaProps } from "./types";

const ArticleMeta: React.FC<ArticleMetaProps> = ({
  authorName,
  publishedAt,
  viewCount,
}) => {
  // Format date to readable string
  const formattedDate = new Date(publishedAt).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  return (
    <div className="blog-article-card__meta">
      <span className="blog-article-card__author">{authorName}</span>
      <span className="blog-article-card__dot" />
      <span>{formattedDate}</span>
      {viewCount > 0 && (
        <>
          <span className="blog-article-card__dot" />
          <span>{viewCount} views</span>
        </>
      )}
    </div>
  );
};

export default ArticleMeta;
