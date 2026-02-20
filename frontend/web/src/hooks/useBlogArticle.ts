/**
 * Custom hook for fetching a single blog article by ID
 * Handles loading and error states
 */

import { useState, useEffect } from 'react';
import { blogApi } from '../utils/blogApi';
import { BlogArticle } from '../types/blog';

interface UseBlogArticleReturn {
  article: BlogArticle | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Fetch a single blog article with full content
 * Automatically increments view count on backend
 * @param articleId - Article ID to fetch
 * @returns Article data, loading state, and error state
 */
export function useBlogArticle(articleId: string | undefined): UseBlogArticleReturn {
  const [article, setArticle] = useState<BlogArticle | null>(null);
  const [loading, setLoading] = useState(() => !!articleId);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!articleId) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchArticle() {
      if (!articleId) return;  // Type guard

      try {
        setLoading(true);
        const data = await blogApi.getArticle(articleId);

        if (!cancelled) {
          setArticle(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
          setArticle(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchArticle();

    // Cleanup function to prevent state updates after unmount
    return () => {
      cancelled = true;
    };
  }, [articleId]);

  return { article, loading, error };
}
