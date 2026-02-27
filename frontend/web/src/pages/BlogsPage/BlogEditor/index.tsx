/**
 * BlogEditor - Create / Edit blog articles
 * Dialog shell + form state + save logic
 *
 * Sub-components:
 *   RichTextEditor   — TipTap WYSIWYG editor (Markdown in/out)
 *   CategorySelect   — Category + Author Type dropdowns
 *   ImageUpload      — Cover image upload
 *   ExitConfirmDialog — Unsaved-changes confirmation popover
 */

import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Label from '@radix-ui/react-label';
import { Cross2Icon } from '@radix-ui/react-icons';
import { blogApi } from '../../../utils/blogApi';
import { BlogArticle } from '../../../types/blog';
import RichTextEditor from './RichTextEditor';
import CategorySelect from './CategorySelect';
import ImageUpload from './ImageUpload';
import ExitConfirmDialog from './ExitConfirmDialog';

interface BlogEditorProps {
  article?: BlogArticle;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved?: (article: BlogArticle) => void;
  userRole?: string | null;
  userName?: string | null;
}

// ─── Types ─────────────────────────────────────────────────────────────────────

interface FormState {
  title: string;
  subtitle: string;
  content: string;
  coverImageUrl: string;
  authorType: 'official' | 'user';
  category: string;
  tags: string;
}

const BlogEditor: React.FC<BlogEditorProps> = ({
  article,
  open,
  onOpenChange,
  onSaved,
  userRole,
  userName,
}) => {
  const isEditMode = Boolean(article);
  const isAdmin = userRole === 'admin';

  // ─── Form state ──────────────────────────────────────────────────────────────

  const defaultForm = (): FormState => ({
    title: '',
    subtitle: '',
    content: '',
    coverImageUrl: '',
    authorType: 'official',
    category: isAdmin ? 'about' : 'user',
    tags: '',
  });

  const [form, setForm] = useState<FormState>(defaultForm);
  const [status, setStatus] = useState<'draft' | 'published'>('draft');
  const [initialForm, setInitialForm] = useState<FormState>(defaultForm);

  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  const set = <K extends keyof FormState>(key: K) =>
    (value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }));

  // ─── Initialise form from article or reset on open ───────────────────────────

  useEffect(() => {
    if (!open) return;
    const initial: FormState = article
      ? {
          title: article.title,
          subtitle: article.subtitle || '',
          content: article.content || '',
          coverImageUrl: article.cover_image_url || '',
          authorType: article.author_type,
          category: article.category,
          tags: article.tags?.join(', ') || '',
        }
      : defaultForm();

    setForm(initial);
    setInitialForm(initial);
    setStatus(article ? (article.status as 'draft' | 'published') : 'draft');
    setError('');
    setShowExitConfirm(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, article]);

  // ─── Image upload ─────────────────────────────────────────────────────────────

  const handleImageUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) { setError('Please select an image file'); return; }
    if (file.size > 5 * 1024 * 1024)    { setError('Image must be less than 5MB');  return; }
    try {
      setUploading(true);
      setError('');
      const result = await blogApi.uploadImage(file);
      set('coverImageUrl')(result.url);
    } catch (err: any) {
      setError(err.message || 'Failed to upload image');
    } finally {
      setUploading(false);
    }
  };

  // ─── Save ─────────────────────────────────────────────────────────────────────

  const handleSave = async (saveStatus: 'draft' | 'published') => {
    if (!form.title.trim())   { setError('Title is required');   return; }
    if (!form.content.trim()) { setError('Content is required'); return; }

    try {
      setSaving(true);
      setError('');

      const payload = {
        title: form.title.trim(),
        subtitle: form.subtitle.trim() || undefined,
        content: form.content.trim(),
        cover_image_url: form.coverImageUrl || undefined,
        author_name: userName || undefined,
        author_type: form.authorType,
        category: form.category,
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
        status: saveStatus,
      };

      const saved = isEditMode && article
        ? await blogApi.updateArticle(article.id, payload)
        : await blogApi.createArticle(payload);

      onSaved?.(saved);
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || 'Failed to save article');
    } finally {
      setSaving(false);
    }
  };

  // ─── Unsaved-changes guard ────────────────────────────────────────────────────

  const hasChanges = () =>
    (Object.keys(initialForm) as (keyof FormState)[]).some(
      (k) => form[k] !== initialForm[k]
    );

  const handleCloseClick = () => {
    if (hasChanges()) setShowExitConfirm(true);
    else onOpenChange(false);
  };

  // ─── Render ───────────────────────────────────────────────────────────────────

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay style={overlayStyle} />
        <Dialog.Content
          style={contentStyle}
          onOpenAutoFocus={(e) => e.preventDefault()}
          onCloseAutoFocus={(e) => e.preventDefault()}
        >

          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', position: 'relative' }}>
            <Dialog.Title style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a' }}>
              {isEditMode ? 'Edit Article' : 'Create New Article'}
            </Dialog.Title>
            <button onClick={handleCloseClick} style={closeButtonStyle}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f0f0f0')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <Cross2Icon width={20} height={20} />
            </button>

            {showExitConfirm && (
              <ExitConfirmDialog
                saving={saving}
                onSaveAndExit={async () => { setShowExitConfirm(false); await handleSave('draft'); }}
                onDiscard={() => { setShowExitConfirm(false); onOpenChange(false); }}
                onCancel={() => setShowExitConfirm(false)}
              />
            )}
          </div>

          {/* Error */}
          {error && (
            <div style={{ padding: '12px 16px', backgroundColor: '#ffebee', color: '#d32f2f', borderRadius: '8px', marginBottom: '16px', fontSize: '0.95rem' }}>
              {error}
            </div>
          )}

          {/* Form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

            {/* Title */}
            <div>
              <Label.Root htmlFor="title" style={labelStyle}>Title *</Label.Root>
              <input
                id="title"
                type="text"
                value={form.title}
                onChange={(e) => set('title')(e.target.value)}
                placeholder="Enter article title..."
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = '#2563eb')}
                onBlur={(e)  => (e.currentTarget.style.borderColor = '#e2e8f0')}
              />
            </div>

            {/* Subtitle */}
            <div>
              <Label.Root htmlFor="subtitle" style={labelStyle}>Subtitle</Label.Root>
              <input
                id="subtitle"
                type="text"
                value={form.subtitle}
                onChange={(e) => set('subtitle')(e.target.value)}
                placeholder="Enter subtitle (optional)..."
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = '#2563eb')}
                onBlur={(e)  => (e.currentTarget.style.borderColor = '#e2e8f0')}
              />
            </div>

            {/* Category + Author Type */}
            <CategorySelect
              isAdmin={isAdmin}
              category={form.category}
              authorType={form.authorType}
              onCategoryChange={set('category')}
              onAuthorTypeChange={set('authorType')}
            />

            {/* Cover Image */}
            <ImageUpload
              coverImageUrl={form.coverImageUrl}
              uploading={uploading}
              onUpload={handleImageUpload}
            />

            {/* Tags */}
            <div>
              <Label.Root htmlFor="tags" style={labelStyle}>Tags</Label.Root>
              <input
                id="tags"
                type="text"
                value={form.tags}
                onChange={(e) => set('tags')(e.target.value)}
                placeholder="Enter tags separated by commas (e.g., tutorial, chess, beginner)"
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = '#2563eb')}
                onBlur={(e)  => (e.currentTarget.style.borderColor = '#e2e8f0')}
              />
            </div>

            {/* Content — Rich Text Editor */}
            <div>
              <Label.Root style={labelStyle}>Content *</Label.Root>
              <RichTextEditor value={form.content} onChange={set('content')} />
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
              <ActionButton onClick={() => handleSave('draft')} disabled={saving || uploading}>
                {saving ? 'Saving...' : 'Save Draft'}
              </ActionButton>
              <ActionButton onClick={() => handleSave('published')} disabled={saving || uploading}>
                {saving ? 'Publishing...' : 'Publish'}
              </ActionButton>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>

      <style>{`
        @keyframes fadeIn  { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp {
          from { opacity: 0; transform: translate(-50%, -45%); }
          to   { opacity: 1; transform: translate(-50%, -50%); }
        }
      `}</style>
    </Dialog.Root>
  );
};

// ─── Shared micro-components ──────────────────────────────────────────────────

const ActionButton: React.FC<{
  onClick: () => void;
  disabled: boolean;
  children: React.ReactNode;
}> = ({ onClick, disabled, children }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      flex: 1,
      padding: '10px 16px',
      fontSize: '0.95rem',
      fontWeight: 500,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
      color: '#2563eb',
      backgroundColor: 'transparent',
      border: '2px solid #2563eb',
      borderRadius: '8px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      transition: 'all 0.2s ease',
    }}
    onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.backgroundColor = 'rgba(37,99,235,0.08)'; }}
    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
    onMouseDown={(e)  => { if (!disabled) e.currentTarget.style.transform = 'scale(0.97)'; }}
    onMouseUp={(e)    => { e.currentTarget.style.transform = 'scale(1)'; }}
  >
    {children}
  </button>
);

// ─── Shared styles ────────────────────────────────────────────────────────────

const overlayStyle: React.CSSProperties = {
  position: 'fixed', inset: 0,
  backgroundColor: 'rgba(0,0,0,0.5)',
  animation: 'fadeIn 0.2s ease',
  zIndex: 9998,
};

const contentStyle: React.CSSProperties = {
  position: 'fixed',
  top: '50%', left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90vw', maxWidth: '900px', maxHeight: '85vh',
  backgroundColor: 'white',
  borderRadius: '8px',
  padding: '24px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
  animation: 'slideUp 0.3s ease',
  zIndex: 9999,
  overflow: 'auto',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, "Helvetica Neue", sans-serif',
};

const closeButtonStyle: React.CSSProperties = {
  border: 'none', background: 'transparent', cursor: 'pointer',
  padding: '8px', borderRadius: '4px',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.95rem', fontWeight: 600, color: '#0f172a',
  marginBottom: '8px', display: 'block',
};

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '12px', fontSize: '1rem',
  border: '1px solid #e2e8f0', borderRadius: '8px',
  outline: 'none', transition: 'border-color 0.2s',
};

export default BlogEditor;
