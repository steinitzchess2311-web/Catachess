/**
 * ArticleCard component - Main integration file
 * Displays blog article preview card with navigation, actions, and metadata
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
        style={{ textDecoration: 'none', display: 'block', height: '100%' }}
      >
        <article
          style={{
            background: "rgba(255, 255, 255, 0.9)",
            borderRadius: "12px",
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
            transition: "all 0.3s ease",
            cursor: "pointer",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            position: "relative",  // For action buttons positioning
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-4px)";
            e.currentTarget.style.boxShadow = "0 8px 24px rgba(0, 0, 0, 0.12)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 2px 12px rgba(0, 0, 0, 0.08)";
          }}
        >
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
            <div
              style={{
                position: "absolute",
                top: "13rem",
                right: "0.75rem",
                display: "flex",
                gap: "0.5rem",
                zIndex: 10,
              }}
            >
              {/* Delete Button */}
              {canDelete && (
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDeleteClick(e);
                  }}
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    border: "none",
                    backgroundColor: "rgba(150, 150, 150, 0.8)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "rgba(220, 53, 69, 0.95)";
                    e.currentTarget.style.transform = "scale(1.1)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "rgba(150, 150, 150, 0.8)";
                    e.currentTarget.style.transform = "scale(1)";
                  }}
                >
                  <TrashIcon width={18} height={18} />
                </button>
              )}

              {/* Pin Button */}
              {canPin && (
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handlePinToggle(e);
                  }}
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    border: "none",
                    backgroundColor: article.is_pinned
                      ? "rgba(255, 193, 7, 0.95)"
                      : "rgba(150, 150, 150, 0.8)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  }}
                  onMouseEnter={(e) => {
                    if (!article.is_pinned) {
                      e.currentTarget.style.backgroundColor = "rgba(255, 193, 7, 0.95)";
                    }
                    e.currentTarget.style.transform = "scale(1.1)";
                  }}
                  onMouseLeave={(e) => {
                    if (!article.is_pinned) {
                      e.currentTarget.style.backgroundColor = "rgba(150, 150, 150, 0.8)";
                    }
                    e.currentTarget.style.transform = "scale(1)";
                  }}
                >
                  <DrawingPinFilledIcon width={18} height={18} />
                </button>
              )}
            </div>
          )}

          {/* Content Section */}
          <div
            style={{
              padding: "20px",
              flex: 1,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <ArticleContent
              title={article.title}
              subtitle={article.subtitle}
            />

            {/* Category Tag — clickable for editors in my-published view */}
            {canChangeCategory && (
              <div style={{ position: "relative", marginBottom: "10px" }}>
                <button
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
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "5px",
                    padding: "4px 10px",
                    borderRadius: "20px",
                    border: "1px solid rgba(139, 115, 85, 0.3)",
                    background: showCategoryDropdown
                      ? "rgba(139, 115, 85, 0.12)"
                      : "rgba(139, 115, 85, 0.06)",
                    color: "#2563eb",
                    fontSize: "0.78rem",
                    fontWeight: 500,
                    cursor: isChangingCategory ? "wait" : "pointer",
                    transition: "all 0.15s ease",
                    letterSpacing: "0.01em",
                  }}
                  onMouseEnter={(e) => {
                    if (!showCategoryDropdown)
                      e.currentTarget.style.background = "rgba(139, 115, 85, 0.12)";
                  }}
                  onMouseLeave={(e) => {
                    if (!showCategoryDropdown)
                      e.currentTarget.style.background = "rgba(139, 115, 85, 0.06)";
                  }}
                >
                  <span>
                    {isChangingCategory
                      ? "Saving…"
                      : (CATEGORY_LABELS[currentCategory] || currentCategory)}
                  </span>
                  <ChevronDownIcon
                    width={12}
                    height={12}
                    style={{
                      transform: showCategoryDropdown ? "rotate(180deg)" : "rotate(0deg)",
                      transition: "transform 0.15s ease",
                    }}
                  />
                </button>

                {showCategoryDropdown && createPortal(
                  <div
                    ref={categoryDropdownRef}
                    style={{
                      position: "fixed",
                      top: dropdownPos.top,
                      left: dropdownPos.left,
                      background: "#fff",
                      borderRadius: "10px",
                      boxShadow: "0 8px 24px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06)",
                      border: "1px solid rgba(139, 115, 85, 0.15)",
                      overflow: "hidden",
                      zIndex: 9999,
                      minWidth: "160px",
                    }}
                  >
                    {SELECTABLE_CATEGORIES.map((cat) => {
                      const isActive = cat.id === currentCategory;
                      return (
                        <button
                          key={cat.id}
                          onClick={(e) => handleCategorySelect(e, cat.id)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            width: "100%",
                            padding: "9px 14px",
                            border: "none",
                            background: isActive ? "rgba(139, 115, 85, 0.08)" : "transparent",
                            color: isActive ? "#2563eb" : "#444",
                            fontSize: "0.83rem",
                            fontWeight: isActive ? 600 : 400,
                            cursor: isActive ? "default" : "pointer",
                            textAlign: "left",
                            transition: "background 0.12s ease",
                            gap: "8px",
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive)
                              e.currentTarget.style.background = "rgba(139, 115, 85, 0.06)";
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive)
                              e.currentTarget.style.background = "transparent";
                          }}
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
