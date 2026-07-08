/**
 * Blog API client
 * Provides methods to interact with backend blog endpoints
 */

import { api } from '@ui/assets/api';
import { BlogArticle, PaginatedResponse, BlogListParams, BlogCategory } from '../types/blog';

const BASE_PATH = '/api/blogs';

type BlogImageType = 'cover' | 'content';
type BlogImageResizeMode = 'original' | 'adaptive_width';

interface BlogImageUploadOptions {
  imageType?: BlogImageType;
  resizeMode?: BlogImageResizeMode;
}

interface BlogImageUploadResponse {
  id: string;
  url: string;
  filename: string;
  size_bytes: number;
  width: number;
  height: number;
  resize_mode: BlogImageResizeMode;
  image_type: BlogImageType;
}

/**
 * Blog API methods
 */
export const blogApi = {
  /**
   * Get paginated list of published articles
   * Supports category filtering and search
   * @param params - Query parameters for filtering and pagination
   * @returns Paginated response with articles
   */
  async getArticles(params: BlogListParams = {}): Promise<PaginatedResponse<BlogArticle>> {
    const query = new URLSearchParams();

    if (params.category) {
      query.append('category', params.category);
    }

    if (params.search) {
      query.append('search', params.search);
    }

    query.append('page', String(params.page || 1));
    query.append('page_size', String(params.page_size || 10));

    const response = await api.get(`${BASE_PATH}/articles?${query}`);
    return response;
  },

  /**
   * Get all pinned articles (for featured section)
   * @returns Array of pinned articles
   */
  async getPinnedArticles(): Promise<BlogArticle[]> {
    const response = await api.get(`${BASE_PATH}/articles/pinned`);
    return response;
  },

  /**
   * Get single article by ID
   * Automatically increments view count
   * @param id - Article ID
   * @returns Full article with content
   */
  async getArticle(id: string): Promise<BlogArticle> {
    const response = await api.get(`${BASE_PATH}/articles/${id}`);
    return response;
  },

  /**
   * Get list of all categories with article counts
   * @returns Array of categories
   */
  async getCategories(): Promise<BlogCategory[]> {
    const response = await api.get(`${BASE_PATH}/categories`);
    return response;
  },

  /**
   * Get user's draft articles
   * Requires Editor or Admin role
   * @returns Array of draft articles
   */
  async getMyDrafts(): Promise<BlogArticle[]> {
    const response = await api.get(`${BASE_PATH}/articles/my-drafts`);
    return response;
  },

  /**
   * Get user's published articles
   * Requires Editor or Admin role
   * @returns Array of published articles
   */
  async getMyPublished(): Promise<BlogArticle[]> {
    const response = await api.get(`${BASE_PATH}/articles/my-published`);
    return response;
  },

  /**
   * Create new article (draft or published)
   * Requires Editor or Admin role
   * @param articleData - Article data
   * @returns Created article
   */
  async createArticle(articleData: {
    title: string;
    subtitle?: string;
    content: string;
    cover_image_url?: string;
    author_name?: string;
    author_type?: 'official' | 'user';  // official: 官方文章 | user: 用户投稿
    category: string;
    sub_category?: string;
    tags?: string[];
    status?: 'draft' | 'published' | 'archived';
    is_pinned?: boolean;
    pin_order?: number;
  }): Promise<BlogArticle> {
    const response = await api.post(`${BASE_PATH}/articles`, articleData);
    return response;
  },

  /**
   * Update existing article
   * Requires ownership or Admin role
   * @param id - Article ID
   * @param articleData - Updated article data
   * @returns Updated article
   */
  async updateArticle(id: string, articleData: Partial<{
    title: string;
    subtitle: string;
    content: string;
    cover_image_url: string;
    author_name: string;
    author_type: 'official' | 'user';  // official: 官方文章 | user: 用户投稿
    category: string;
    sub_category: string;
    tags: string[];
    status: 'draft' | 'published' | 'archived';
    is_pinned: boolean;
    pin_order: number;
  }>): Promise<BlogArticle> {
    const response = await api.put(`${BASE_PATH}/articles/${id}`, articleData);
    return response;
  },

  /**
   * Delete article
   * Requires ownership or Admin role
   * @param id - Article ID
   */
  async deleteArticle(id: string): Promise<void> {
    await api.delete(`${BASE_PATH}/articles/${id}`);
  },

  /**
   * Upload image to R2 storage
   * Requires Editor or Admin role
   * @param file - Image file
   * @returns Image URL
   */
  async uploadImage(
    file: File,
    options: BlogImageUploadOptions = {}
  ): Promise<BlogImageUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('image_type', options.imageType || 'content');
    formData.append('resize_mode', options.resizeMode || 'adaptive_width');
    const response = await api.post(`${BASE_PATH}/upload-image`, formData);
    return response;
  },

  /**
   * Toggle like on an article (requires login)
   * @param id - Article ID
   * @returns { liked: boolean, like_count: number }
   */
  async toggleLike(id: string): Promise<{ liked: boolean; like_count: number }> {
    const response = await api.post(`${BASE_PATH}/articles/${id}/like`, {});
    return response;
  },

  /**
   * Pin or unpin article
   * Requires Admin role
   * @param id - Article ID
   * @param pinOrder - Pin priority (0 to unpin, >0 to pin)
   */
  async pinArticle(id: string, pinOrder: number): Promise<{
    success: boolean;
    message: string;
    is_pinned: boolean;
    pin_order: number;
  }> {
    const response = await api.post(`${BASE_PATH}/articles/${id}/pin?pin_order=${pinOrder}`);
    return response;
  }
};
