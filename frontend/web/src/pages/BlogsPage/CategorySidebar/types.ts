/**
 * CategorySidebar types
 */

export type ViewMode = 'articles' | 'drafts' | 'my-published';

export interface CategorySidebarProps {
  activeCategory?: string;
  searchQuery?: string;
  onCategoryChange: (category: string | undefined) => void;
  onSearchChange: (search: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  userRole: string | null;
  userName: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export interface ToggleButtonProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export interface PinnedButtonProps {
  activeCategory?: string;
  onCategoryChange: (category: string | undefined) => void;
  onViewModeChange: (mode: ViewMode) => void;
}

export interface OfficialSectionProps {
  activeCategory?: string;
  isOfficialOpen: boolean;
  setIsOfficialOpen: (open: boolean) => void;
  onCategoryClick: (categoryId: string) => void;
}

export interface CommunityButtonProps {
  activeCategory?: string;
  onUserBlogsClick: () => void;
}

export interface SearchSectionProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  handleSearchClear: () => void;
}

export interface UserActionsSectionProps {
  userRole: string | null;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  setEditorOpen: (open: boolean) => void;
}

export interface CollapsedViewProps {
  activeCategory?: string;
  onCategoryChange: (category: string | undefined) => void;
  onViewModeChange: (mode: ViewMode) => void;
  onUserBlogsClick: () => void;
  userRole: string | null;
  setEditorOpen: (open: boolean) => void;
}
