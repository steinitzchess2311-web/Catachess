/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ArticleContent component - title and summary display.
 */

import React from "react";
import { ArticleContentProps } from "./types";

const ArticleContent: React.FC<ArticleContentProps> = ({ title, subtitle }) => {
  return (
    <>
      <h3 className="blog-article-card__title">
        {title}
      </h3>

      <p className="blog-article-card__subtitle">
        {subtitle}
      </p>
    </>
  );
};

export default ArticleContent;
