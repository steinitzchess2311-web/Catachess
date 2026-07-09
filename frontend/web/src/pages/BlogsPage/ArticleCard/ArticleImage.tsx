/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ArticleImage component - cover image for article preview cards.
 */

import React from "react";
import { ArticleImageProps } from "./types";
import logoImage from "../../../assets/logo.jpg";

const ArticleImage: React.FC<ArticleImageProps> = ({
  imageUrl,
  title,
  category,
  isPinned,
}) => {
  const displayImage = imageUrl || logoImage;

  return (
    <div className="blog-article-card__media">
      <img
        src={displayImage}
        alt={title}
        className="blog-article-card__image"
      />
    </div>
  );
};

export default ArticleImage;
