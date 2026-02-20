/**
 * Type definitions for ArticleCard component
 */

import { BlogArticle } from "../../../types/blog";

export type ViewMode = 'articles' | 'drafts' | 'my-published';

export interface ArticleCardProps {
  article: BlogArticle;
  userRole?: string | null;
  viewMode?: ViewMode;
  onDelete?: (articleId: string) => void;
  onPinToggle?: (articleId: string) => void;
  onCategoryChange?: (articleId: string, newCategory: string) => void;
}

export interface ArticleImageProps {
  imageUrl: string;
  title: string;
  category: string;
  isPinned: boolean;
}

export interface ArticleContentProps {
  title: string;
  subtitle: string;
}

export interface ArticleMetaProps {
  authorName: string;
  publishedAt: string;
  viewCount: number;
}

export interface ActionButtonsProps {
  canDelete: boolean;
  canPin: boolean;
  isDeleting: boolean;
  isPinning: boolean;
  isPinned: boolean;
  onDeleteClick: (e: React.MouseEvent) => void;
  onPinToggle: (e: React.MouseEvent) => void;
  deleteButtonRef: React.RefObject<HTMLButtonElement>;
  showDeleteConfirm: boolean;
  dialogRef: React.RefObject<HTMLDivElement>;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}

export interface DeleteConfirmDialogProps {
  show: boolean;
  dialogRef: React.RefObject<HTMLDivElement>;
  onConfirm: () => void;
  onCancel: () => void;
}

export const CATEGORY_LABELS: { [key: string]: string } = {
  'about': 'Our Stories',
  'function': 'Functions Intro',
  'devlog': 'Developer Logs',
  'allblogs': 'Blog',
  'user': 'User'
};

export const SELECTABLE_CATEGORIES = [
  { id: 'about', label: 'Our Stories' },
  { id: 'function', label: 'Functions Intro' },
  { id: 'devlog', label: 'Developer Logs' },
  { id: 'user', label: 'User' },
];
