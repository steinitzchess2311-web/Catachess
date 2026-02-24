/**
 * ArticleContent component - Title and subtitle display
 */

import React from "react";
import { ArticleContentProps } from "./types";

const ArticleContent: React.FC<ArticleContentProps> = ({ title, subtitle }) => {
  return (
    <>
      {/* Title */}
      <h3
        style={{
          fontSize: "1.3rem",
          fontWeight: 700,
          color: "#0f172a",
          marginBottom: "10px",
          lineHeight: "1.4",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {title}
      </h3>

      {/* Subtitle */}
      <p
        style={{
          fontSize: "0.95rem",
          color: "#475569",
          lineHeight: "1.6",
          marginBottom: "16px",
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          textOverflow: "ellipsis",
          flex: 1,
        }}
      >
        {subtitle}
      </p>
    </>
  );
};

export default ArticleContent;
