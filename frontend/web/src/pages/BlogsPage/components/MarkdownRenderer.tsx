/**
 * Markdown content renderer component
 * Uses react-markdown with GitHub-flavored markdown support
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
    <div
      style={{
        fontSize: '1.05rem',
        lineHeight: '1.8',
        color: '#0f172a',
        marginTop: '32px'
      }}
      className="markdown-content"
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} children={content} />
    </div>
  );
};

export default MarkdownRenderer;
