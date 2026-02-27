/**
 * TypeScript type definitions for Blog API
 * Based on backend API documentation
 */

/**
 * Blog article entity with all fields returned from API
 */
export interface BlogArticle {
  id: string;
  title: string;
  subtitle: string;
  content?: string;  // Only included in detail view
  cover_image_url: string;
  author_id?: string;  // UUID of author, only in detail view
  author_name: string;
  author_type: 'official' | 'user';  // official: 官方文章 | user: 用户投稿
  category: 'about' | 'function' | 'allblogs' | 'user';
  tags: string[];
  status?: 'draft' | 'published' | 'archived';  // Only in detail/my views
  is_pinned: boolean;
  view_count: number;
  like_count: number;
  comment_count: number;
  is_liked?: boolean;   // Whether the current logged-in user has liked this article
  created_at: string;  // ISO 8601 date string
  published_at: string;  // ISO 8601 date string
}

/**
 * Paginated API response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * Parameters for fetching blog article list
 */
export interface BlogListParams {
  category?: string;  // Filter by category
  search?: string;    // Search in title and content
  page?: number;      // Page number (1-indexed)
  page_size?: number; // Items per page
}

/**
 * Blog category metadata
 */
export interface BlogCategory {
  id: string;
  name: string;
  description?: string;
  article_count: number;
}
