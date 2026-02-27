import { api } from '@ui/assets/api';
import { Comment } from '../types/comment';

const BASE = '/api/blogs';

export const commentApi = {
  /** Fetch all comments for an article (flat list) */
  list(articleId: string): Promise<{ items: Comment[]; total: number }> {
    return api.get(`${BASE}/articles/${articleId}/comments`);
  },

  /** Post a new comment or reply */
  create(articleId: string, body: {
    content: string;
    parent_id?: string | null;
    quote_id?: string | null;
  }): Promise<Comment> {
    return api.post(`${BASE}/articles/${articleId}/comments`, body);
  },

  /** Edit a comment — must pass current version for optimistic lock */
  edit(commentId: string, content: string, version: number): Promise<Comment> {
    return api.put(`${BASE}/comments/${commentId}`, { content, version });
  },

  /** Soft-delete a comment */
  delete(commentId: string): Promise<void> {
    return api.delete(`${BASE}/comments/${commentId}`);
  },

  /** Toggle like on a comment */
  toggleLike(commentId: string): Promise<{ liked: boolean; like_count: number }> {
    return api.post(`${BASE}/comments/${commentId}/like`, {});
  },
};
