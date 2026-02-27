/**
 * Comment type definitions
 */

export interface Comment {
  id: string;
  article_id: string;
  parent_id: string | null;
  quote_id: string | null;
  author_id: string;
  author_name: string;
  content: string;
  is_deleted: boolean;
  edited: boolean;
  like_count: number;
  is_liked: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

/** Client-side tree node — same as Comment but with resolved children */
export interface CommentNode extends Comment {
  children: CommentNode[];
}
