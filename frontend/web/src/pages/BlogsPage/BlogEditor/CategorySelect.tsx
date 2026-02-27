/**
 * CategorySelect - Category + Author Type selectors for BlogEditor
 * Admin: full category choice; non-admin: fixed to User Content
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
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
      {/* Category */}
      <div>
        <Label.Root
          style={{ fontSize: '0.95rem', fontWeight: 600, color: '#0f172a', marginBottom: '8px', display: 'block' }}
        >
          Category *
        </Label.Root>
        {isAdmin ? (
          <Select.Root value={category} onValueChange={onCategoryChange}>
            <Select.Trigger style={triggerStyle}>
              <Select.Value />
              <Select.Icon><ChevronDownIcon /></Select.Icon>
            </Select.Trigger>
            <Select.Portal>
              <Select.Content style={contentStyle}>
                <Select.Viewport>
                  <Select.Group>
                    <Select.Label style={groupLabelStyle}>📖 ChessorTag Official</Select.Label>
                    <SelectItem value="about">Our Stories</SelectItem>
                    <SelectItem value="function">Function Intro</SelectItem>
                    <SelectItem value="devlog">Developer Logs</SelectItem>
                  </Select.Group>
                  <Select.Separator style={{ height: '1px', backgroundColor: '#e2e8f0', margin: '8px 0' }} />
                  <Select.Group>
                    <Select.Label style={groupLabelStyle}>✍️ Community</Select.Label>
                    <SelectItem value="user">User Content</SelectItem>
                  </Select.Group>
                </Select.Viewport>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
        ) : (
          <div style={fixedFieldStyle}>✍️ Community (User Content)</div>
        )}
      </div>

      {/* Author Type */}
      <div>
        <Label.Root
          style={{ fontSize: '0.95rem', fontWeight: 600, color: '#0f172a', marginBottom: '8px', display: 'block' }}
        >
          Author Type
        </Label.Root>
        <Select.Root value={authorType} onValueChange={(v) => onAuthorTypeChange(v as 'official' | 'user')}>
          <Select.Trigger style={triggerStyle}>
            <Select.Value />
            <Select.Icon><ChevronDownIcon /></Select.Icon>
          </Select.Trigger>
          <Select.Portal>
            <Select.Content style={contentStyle}>
              <Select.Viewport>
                <SelectItem value="official">📖 Official (ChessorTag)</SelectItem>
                <SelectItem value="user">✍️ User Contribution</SelectItem>
              </Select.Viewport>
            </Select.Content>
          </Select.Portal>
        </Select.Root>
      </div>
    </div>
  );
};

// ─── shared styles ────────────────────────────────────────────────────────────

const triggerStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px',
  fontSize: '1rem',
  border: '1px solid #e2e8f0',
  borderRadius: '8px',
  backgroundColor: 'white',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  cursor: 'pointer',
};

const contentStyle: React.CSSProperties = {
  backgroundColor: 'white',
  borderRadius: '8px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
  padding: '8px',
  zIndex: 10000,
};

const groupLabelStyle: React.CSSProperties = {
  padding: '8px 12px',
  fontSize: '0.8rem',
  color: '#2563eb',
  fontWeight: 700,
};

const fixedFieldStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px',
  fontSize: '1rem',
  border: '1px solid #e2e8f0',
  borderRadius: '8px',
  backgroundColor: '#f5f5f5',
  color: '#475569',
};

// ─── SelectItem helper ────────────────────────────────────────────────────────

const SelectItem = React.forwardRef<HTMLDivElement, { value: string; children: React.ReactNode }>(
  ({ value, children }, ref) => (
    <Select.Item
      value={value}
      ref={ref}
      style={{
        padding: '10px 12px',
        fontSize: '0.95rem',
        borderRadius: '6px',
        cursor: 'pointer',
        outline: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        userSelect: 'none',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f5f5f5')}
      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
    >
      <Select.ItemText>{children}</Select.ItemText>
      <Select.ItemIndicator><CheckIcon /></Select.ItemIndicator>
    </Select.Item>
  )
);
SelectItem.displayName = 'SelectItem';

export default CategorySelect;
