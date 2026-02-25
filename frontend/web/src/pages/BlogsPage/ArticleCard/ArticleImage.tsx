/**
 * ArticleImage component - Cover image with category and pinned badges
 */

import React from "react";
import { ArticleImageProps, CATEGORY_LABELS } from "./types";
import logoImage from "../../../assets/logo.jpg";

const ArticleImage: React.FC<ArticleImageProps> = ({
  imageUrl,
  title,
  category,
  isPinned,
}) => {
  const displayImage = imageUrl || logoImage;

  return (
    <div
      style={{
        width: "100%",
        aspectRatio: "16 / 10",
        overflow: "hidden",
        position: "relative",
        backgroundColor: "#f5f5f5",
      }}
    >
      <img
        src={displayImage}
        alt={title}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transition: "transform 0.3s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.05)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)";
        }}
      />
    </div>
  );
};

export default ArticleImage;
