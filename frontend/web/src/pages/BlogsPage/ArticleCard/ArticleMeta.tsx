/**
 * ArticleMeta component - Author, date, and view count metadata
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
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        paddingTop: "12px",
        borderTop: "1px solid rgba(139, 115, 85, 0.1)",
        fontSize: "0.85rem",
        color: "#2563eb",
      }}
    >
      <span style={{ fontWeight: 600 }}>{authorName}</span>
      <span style={{ color: "#d0d0d0" }}>•</span>
      <span>{formattedDate}</span>
      {viewCount > 0 && (
        <>
          <span style={{ color: "#d0d0d0" }}>•</span>
          <span>{viewCount} views</span>
        </>
      )}
    </div>
  );
};

export default ArticleMeta;
