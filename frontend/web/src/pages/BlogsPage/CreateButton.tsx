/**
 * CreateButton component - Button for creating blog articles
 * Shows for authenticated users with Editor or Admin role
 * Positioned in top-right corner of ContentArea
 */

import React, { useState } from 'react';
import BlogEditor from './BlogEditor';
import { BlogArticle } from '../../types/blog';

interface CreateButtonProps {
  onArticleCreated?: (article: BlogArticle) => void;
  userRole?: string | null;  // Pass to BlogEditor
}

/**
 * Create article button positioned in top-right
 */
const CreateButton: React.FC<CreateButtonProps> = ({ onArticleCreated, userRole }) => {
  const [editorOpen, setEditorOpen] = useState(false);

  const handleArticleSaved = (article: BlogArticle) => {
    // Show success notification
    alert(`Article "${article.title}" saved successfully! ${article.status === 'published' ? 'It will appear in the blog list.' : 'It\'s saved as a draft.'}`);

    // Call callback
    onArticleCreated?.(article);

    // Reload to show new article (won't cause logout if done properly)
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  return (
    <>
      {/* Create Button - Top Right */}
      <button
        onClick={() => setEditorOpen(true)}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          padding: '10px 20px',
          fontSize: '0.95rem',
          fontWeight: 600,
          color: 'white',
          backgroundColor: '#2563eb',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s ease',
          zIndex: 10
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#1d4ed8';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(37, 99, 235, 0.4)';
          e.currentTarget.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#2563eb';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(37, 99, 235, 0.3)';
          e.currentTarget.style.transform = 'translateY(0)';
        }}
        title="Create New Article"
      >
        <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>+</span>
        <span>Create Article</span>
      </button>

      {/* Blog Editor Modal */}
      <BlogEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        onSaved={handleArticleSaved}
        userRole={userRole}
      />
    </>
  );
};

export default CreateButton;
