/**
 * Created at: 2026-07-09 01:42 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:42 EDT
 * Last Modified by: Codex
 *
 * MarkdownRenderer - renders article Markdown with GitHub-flavored syntax.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
}

/**
 * Renders markdown content with custom styling
 * Supports GFM features (tables, strikethrough, task lists, etc.)
 */
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]} children={content} />
    </div>
  );
};

export default MarkdownRenderer;
