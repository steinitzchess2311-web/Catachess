/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:34 EDT
 * Last Modified by: Codex
 *
 * CategorySidebar component - blog navigation and author actions.
 */

import React, { useState, useEffect } from "react";
import BlogEditor from "../BlogEditor/index";
import ToggleButton from "./ToggleButton";
import OfficialSection from "./OfficialSection";
import PinnedButton from "./PinnedButton";
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
  const [isOfficialOpen, setIsOfficialOpen] = useState<boolean>(true);
  const [editorOpen, setEditorOpen] = useState<boolean>(false);

  useEffect(() => {
    if (['about', 'function', 'devlog', 'official'].includes(activeCategory ?? '')) {
      setIsOfficialOpen(true);
    }
  }, [activeCategory]);

  const handleUserBlogsClick = () => {
    // Community is now enabled - navigate to user category (also resets viewMode via handleCategoryClick)
    handleCategoryClick('user');
  };

  // Handle category click — also resets viewMode to 'articles'
  const handleCategoryClick = (categoryId: string) => {
    const categoryMap: { [key: string]: string | undefined } = {
      'about': 'about',
      'function': 'function',
      'devlog': 'devlog',
      'allblogs': 'official',
      'user': 'user',
      'pinned': 'pinned',
    };

    onViewModeChange('articles');
    onCategoryChange(categoryMap[categoryId]);
  };

  return (
    <>
      <div
        className={`blog-sidebar${isOpen ? ' is-open' : ' is-collapsed'}`}
      >
        {/* Toggle Button */}
        <ToggleButton isOpen={isOpen} onOpenChange={onOpenChange} />

        {isOpen && (
          <>
            <div className="blog-sidebar__nav">
              {/* When in drafts/my-published mode, no category should appear highlighted */}
              {(() => {
                const displayCategory = viewMode === 'articles' ? activeCategory : '__none__';
                return (
                  <>
                    {/* Community */}
                    <CommunityButton
                      activeCategory={displayCategory}
                      onUserBlogsClick={handleUserBlogsClick}
                    />

                    {/* Chessortag Official - Collapsible */}
                    <OfficialSection
                      activeCategory={displayCategory}
                      isOfficialOpen={isOfficialOpen}
                      setIsOfficialOpen={setIsOfficialOpen}
                      onCategoryClick={handleCategoryClick}
                    />

                    {/* Pinned Articles — same level as Community & Official */}
                    <PinnedButton
                      activeCategory={displayCategory}
                      onCategoryChange={onCategoryChange}
                      onViewModeChange={onViewModeChange}
                    />
                  </>
                );
              })()}
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
            activeCategory={viewMode === 'articles' ? activeCategory : '__none__'}
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

    </>
  );
};

export default CategorySidebar;
