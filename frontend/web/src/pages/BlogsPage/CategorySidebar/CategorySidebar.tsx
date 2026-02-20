/**
 * CategorySidebar component - Blog navigation and search (Main integration file)
 * Provides category filtering and search functionality
 */

import React, { useState, useEffect } from "react";
import BlogEditor from "../BlogEditor";
import ToggleButton from "./ToggleButton";
import PinnedButton from "./PinnedButton";
import OfficialSection from "./OfficialSection";
import CommunityButton from "./CommunityButton";
import UserActionsSection from "./UserActionsSection";
import CollapsedView from "./CollapsedView";
import { CategorySidebarProps } from "./types";

/**
 * Sidebar for blog navigation with category filtering and search
 */
const CategorySidebar: React.FC<CategorySidebarProps> = ({
  activeCategory,
  searchQuery: externalSearchQuery = "",
  onCategoryChange,
  onSearchChange,
  viewMode,
  onViewModeChange,
  userRole,
  userName,
  isOpen,
  onOpenChange,
}) => {
  const [isOfficialOpen, setIsOfficialOpen] = useState<boolean>(false);
  const [showComingSoon, setShowComingSoon] = useState<boolean>(false);
  const [editorOpen, setEditorOpen] = useState<boolean>(false);

  const handleUserBlogsClick = () => {
    // Community is now enabled - navigate to user category
    handleCategoryClick('user');
  };

  // Handle category click
  const handleCategoryClick = (categoryId: string) => {
    // Map UI category IDs to API category values
    const categoryMap: { [key: string]: string | undefined } = {
      'about': 'about',
      'function': 'function',
      'devlog': 'devlog',
      'allblogs': 'official',  // Chessortag Official - all official blogs
      'user': 'user',  // Community category
    };

    onCategoryChange(categoryMap[categoryId]);
  };

  return (
    <>
      {/* Coming Soon Modal */}
      {showComingSoon && (
        <div
          style={{
            position: "fixed",
            top: "80px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(44, 44, 44, 0.95)",
            color: "white",
            padding: "12px 32px",
            borderRadius: "8px",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.25)",
            zIndex: 9999,
            fontSize: "1.3rem",
            fontWeight: 600,
            animation: "slideDown 0.3s ease",
          }}
        >
          Coming Soon ✨
        </div>
      )}

      <div
        style={{
          width: isOpen ? "280px" : "60px",
          flexShrink: 0,
          background: "rgba(255, 255, 255, 0.85)",
          borderRadius: "12px",
          padding: isOpen ? "25px 0" : "16px 0",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
          position: "sticky",
          top: "0",
          alignSelf: "flex-start",
          transition: "width 0.3s ease, padding 0.3s ease",
          overflow: isOpen ? "visible" : "hidden",
        }}
      >
        {/* Toggle Button */}
        <ToggleButton isOpen={isOpen} onOpenChange={onOpenChange} />

        {isOpen && (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "48px" }}>
              {/* Pinned Articles */}
              <PinnedButton
                activeCategory={activeCategory}
                onCategoryChange={onCategoryChange}
                onViewModeChange={onViewModeChange}
              />

              {/* Community */}
              <CommunityButton
                activeCategory={activeCategory}
                onUserBlogsClick={handleUserBlogsClick}
              />

              {/* Chessortag Official - Collapsible */}
              <OfficialSection
                activeCategory={activeCategory}
                isOfficialOpen={isOfficialOpen}
                setIsOfficialOpen={setIsOfficialOpen}
                onCategoryClick={handleCategoryClick}
              />
            </div>

            {/* User Actions Section - Only show for Editor/Admin */}
            <UserActionsSection
              userRole={userRole}
              viewMode={viewMode}
              onViewModeChange={onViewModeChange}
              setEditorOpen={setEditorOpen}
            />
          </>
        )}

        {/* Collapsed State - Minimal Icon View */}
        {!isOpen && (
          <CollapsedView
            activeCategory={activeCategory}
            isOfficialOpen={isOfficialOpen}
            setIsOfficialOpen={setIsOfficialOpen}
            onCategoryChange={onCategoryChange}
            onViewModeChange={onViewModeChange}
            onUserBlogsClick={handleUserBlogsClick}
            userRole={userRole}
            setEditorOpen={setEditorOpen}
          />
        )}
      </div>

      {/* Blog Editor Dialog */}
      <BlogEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        onSaved={(savedArticle) => {
          // Close the editor
          setEditorOpen(false);
          // Refresh the page to show the new/updated article
          window.location.reload();
        }}
        userRole={userRole}
        userName={userName}
      />

      <style>
        {`
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }

          @keyframes shake {
            0%, 100% {
              transform: translateX(0);
            }
            10%, 30%, 50%, 70%, 90% {
              transform: translateX(-4px);
            }
            20%, 40%, 60%, 80% {
              transform: translateX(4px);
            }
          }
        `}
      </style>
    </>
  );
};

export default CategorySidebar;
