/**
 * Created at: 2026-07-09 01:31 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:31 EDT
 * Last Modified by: Codex
 *
 * CategorySelect - category and author type selectors for BlogEditor.
 */

import React from 'react';
import * as Select from '@radix-ui/react-select';
import * as Label from '@radix-ui/react-label';
import { ChevronDownIcon, CheckIcon } from '@radix-ui/react-icons';

interface CategorySelectProps {
  isAdmin: boolean;
  category: string;
  authorType: 'official' | 'user';
  onCategoryChange: (value: string) => void;
  onAuthorTypeChange: (value: 'official' | 'user') => void;
}

const CategorySelect: React.FC<CategorySelectProps> = ({
  isAdmin,
  category,
  authorType,
  onCategoryChange,
  onAuthorTypeChange,
}) => {
  return (
    <div className="blog-editor-grid">
      {/* Category */}
      <div className="blog-editor-field">
        <Label.Root className="blog-editor-label">
          Category *
        </Label.Root>
        {isAdmin ? (
          <Select.Root value={category} onValueChange={onCategoryChange}>
            <Select.Trigger className="blog-editor-select-trigger">
              <Select.Value />
              <Select.Icon><ChevronDownIcon /></Select.Icon>
            </Select.Trigger>
            <Select.Portal>
              <Select.Content className="blog-editor-select-content">
                <Select.Viewport>
                  <Select.Group>
                    <Select.Label className="blog-editor-select-label">ChessorTag Official</Select.Label>
                    <SelectItem value="about">Our Stories</SelectItem>
                    <SelectItem value="function">Function Intro</SelectItem>
                    <SelectItem value="devlog">Developer Logs</SelectItem>
                  </Select.Group>
                  <Select.Separator className="blog-editor-select-separator" />
                  <Select.Group>
                    <Select.Label className="blog-editor-select-label">Community</Select.Label>
                    <SelectItem value="user">User Content</SelectItem>
                  </Select.Group>
                </Select.Viewport>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
        ) : (
          <div className="blog-editor-fixed-field">Community</div>
        )}
      </div>

      {/* Author Type */}
      <div className="blog-editor-field">
        <Label.Root className="blog-editor-label">
          Author Type
        </Label.Root>
        <Select.Root value={authorType} onValueChange={(v) => onAuthorTypeChange(v as 'official' | 'user')}>
          <Select.Trigger className="blog-editor-select-trigger">
            <Select.Value />
            <Select.Icon><ChevronDownIcon /></Select.Icon>
          </Select.Trigger>
          <Select.Portal>
            <Select.Content className="blog-editor-select-content">
              <Select.Viewport>
                <SelectItem value="official">Official</SelectItem>
                <SelectItem value="user">User</SelectItem>
              </Select.Viewport>
            </Select.Content>
          </Select.Portal>
        </Select.Root>
      </div>
    </div>
  );
};

const SelectItem = React.forwardRef<HTMLDivElement, { value: string; children: React.ReactNode }>(
  ({ value, children }, ref) => (
    <Select.Item
      value={value}
      ref={ref}
      className="blog-editor-select-item"
    >
      <Select.ItemText>{children}</Select.ItemText>
      <Select.ItemIndicator><CheckIcon /></Select.ItemIndicator>
    </Select.Item>
  )
);
SelectItem.displayName = 'SelectItem';

export default CategorySelect;
