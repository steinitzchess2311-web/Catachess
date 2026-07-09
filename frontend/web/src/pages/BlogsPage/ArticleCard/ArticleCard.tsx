/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ArticleCard component - article preview card with management actions.
 *
 * This is the main component that orchestrates all sub-components:
 * - ArticleImage: Cover image with badges
 * - ArticleContent: Title and subtitle
 * - ArticleMeta: Author, date, view count
 * - ActionButtons: Delete and pin buttons
 * - DeleteConfirmDialog: Confirmation dialog
 */

import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { TrashIcon, DrawingPinFilledIcon, ChevronDownIcon, CheckIcon } from "@radix-ui/react-icons";
import { ArticleCardProps, CATEGORY_LABELS, SELECTABLE_CATEGORIES } from "./types";
import { blogApi } from "../../../utils/blogApi";
import ArticleImage from "./ArticleImage";
import ArticleContent from "./ArticleContent";
import ArticleMeta from "./ArticleMeta";
import DeleteConfirmDialog from "./DeleteConfirmDialog";

const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  userRole,
  viewMode = 'articles',
  onDelete,
  onPinToggle,
  onCategoryChange,
}) => {
  // State
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPinning, setIsPinning] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [currentCategory, setCurrentCategory] = useState(article.category);
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [isChangingCategory, setIsChangingCategory] = useState(false);
  const [dropdownPos, setDropdownPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const categoryChipRef = useRef<HTMLButtonElement>(null);
  const categoryDropdownRef = useRef<HTMLDivElement>(null);

  // Refs for dialog positioning and click-outside detection
  const dialogRef = useRef<HTMLDivElement>(null);

  // Permission checks
  const canDelete =
    userRole === 'admin' ||
    (userRole === 'editor' && (viewMode === 'drafts' || viewMode === 'my-published'));
  const canPin = userRole === 'admin';
  const canChangeCategory =
    (userRole === 'editor' || userRole === 'admin') && viewMode === 'my-published';

  // Handle click outside category dropdown
  useEffect(() => {
    if (!showCategoryDropdown) return;
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      const inDropdown = categoryDropdownRef.current?.contains(target);
      const inChip = categoryChipRef.current?.contains(target);
      if (!inDropdown && !inChip) setShowCategoryDropdown(false);
    };
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);
    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showCategoryDropdown]);

  const handleCategorySelect = async (e: React.MouseEvent, categoryId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (categoryId === currentCategory || isChangingCategory) return;
    setShowCategoryDropdown(false);
    setIsChangingCategory(true);
    try {
      await blogApi.updateArticle(article.id, { category: categoryId });
      setCurrentCategory(categoryId);
      if (onCategoryChange) onCategoryChange(article.id, categoryId);
    } catch (error) {
      console.error('Failed to change category:', error);
    } finally {
      setIsChangingCategory(false);
    }
  };

  // Handle click outside dialog to close it
  useEffect(() => {
    if (!showDeleteConfirm) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dialogRef.current &&
        !dialogRef.current.contains(event.target as Node)
      ) {
        setShowDeleteConfirm(false);
      }
    };

    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDeleteConfirm]);

  // Event handlers
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    setShowDeleteConfirm(false);
    setIsDeleting(true);
    try {
      await blogApi.deleteArticle(article.id);
      if (onDelete) {
        onDelete(article.id);
      }
    } catch (error) {
      console.error('Failed to delete article:', error);
      alert('Failed to delete article. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const handlePinToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setIsPinning(true);
    try {
      const newPinOrder = article.is_pinned ? 0 : 1;
      await blogApi.pinArticle(article.id, newPinOrder);
      if (onPinToggle) {
        onPinToggle(article.id);
      }
    } catch (error) {
      console.error('Failed to toggle pin:', error);
      alert('Failed to toggle pin. Please try again.');
    } finally {
      setIsPinning(false);
    }
  };

  return (
    <>
      <Link
        to={`/blogs/${article.id}`}
        className="blog-article-card-link"
      >
        <article className="blog-article-card">
          {/* Delete Confirmation Dialog */}
          <DeleteConfirmDialog
            show={showDeleteConfirm && canDelete}
            dialogRef={dialogRef}
            onConfirm={confirmDelete}
            onCancel={cancelDelete}
          />
          {/* Cover Image Section */}
          <ArticleImage
            imageUrl={article.cover_image_url}
            title={article.title}
            category={article.category}
            isPinned={article.is_pinned}
          />

          {/* Action Buttons - Below Image */}
          {(canDelete || canPin) && (
            <div className="blog-article-card__actions">
              {/* Delete Button */}
              {canDelete && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDeleteClick(e);
                  }}
                  className="blog-article-card__action-button is-danger"
                  aria-label="Delete article"
                >
                  <TrashIcon width={18} height={18} />
                </button>
              )}

              {/* Pin Button */}
              {canPin && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handlePinToggle(e);
                  }}
                  className={`blog-article-card__action-button is-pin${article.is_pinned ? ' is-active' : ''}`}
                  aria-label={article.is_pinned ? "Unpin article" : "Pin article"}
                >
                  <DrawingPinFilledIcon width={18} height={18} />
                </button>
              )}
            </div>
          )}

          {/* Content Section */}
          <div
            className="blog-article-card__body"
          >
            <ArticleContent
              title={article.title}
              subtitle={article.subtitle}
            />

            {/* Category Tag — clickable for editors in my-published view */}
            {canChangeCategory && (
              <div className="blog-article-card__category-wrap">
                <button
                  type="button"
                  ref={categoryChipRef}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (isChangingCategory) return;
                    if (!showCategoryDropdown && categoryChipRef.current) {
                      const rect = categoryChipRef.current.getBoundingClientRect();
                      setDropdownPos({ top: rect.bottom + 6, left: rect.left });
                    }
                    setShowCategoryDropdown(prev => !prev);
                  }}
                  className={`blog-article-card__category${showCategoryDropdown ? ' is-open' : ''}`}
                >
                  <span>
                    {isChangingCategory
                      ? "Saving…"
                      : (CATEGORY_LABELS[currentCategory] || currentCategory)}
                  </span>
                  <ChevronDownIcon
                    width={12}
                    height={12}
                    className="blog-article-card__category-icon"
                  />
                </button>

                {showCategoryDropdown && createPortal(
                  <div
                    ref={categoryDropdownRef}
                    className="blog-category-menu"
                    style={{ top: dropdownPos.top, left: dropdownPos.left }}
                  >
                    {SELECTABLE_CATEGORIES.map((cat) => {
                      const isActive = cat.id === currentCategory;
                      return (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={(e) => handleCategorySelect(e, cat.id)}
                          className={`blog-category-menu__item${isActive ? ' is-active' : ''}`}
                        >
                          <span>{cat.label}</span>
                          {isActive && <CheckIcon width={14} height={14} />}
                        </button>
                      );
                    })}
                  </div>,
                  document.body
                )}
              </div>
            )}

            <ArticleMeta
              authorName={article.author_name}
              publishedAt={article.published_at}
              viewCount={article.view_count}
            />
          </div>
        </article>
      </Link>
    </>
  );
};

export default ArticleCard;
