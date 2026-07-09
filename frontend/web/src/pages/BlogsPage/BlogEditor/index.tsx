/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:44 EDT
 * Last Modified by: Codex
 *
 * BlogEditor - create/edit blog articles with metadata, cover, and content.
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

  const handleImageUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) { setError('Please select an image file'); return; }
    if (file.size > 5 * 1024 * 1024)    { setError('Image must be less than 5MB');  return; }
    try {
      setUploading(true);
      setError('');
      const result = await blogApi.uploadImage(file, { imageType: 'cover' });
      set('coverImageUrl')(result.url);
    } catch (err: any) {
      setError(err.message || 'Failed to upload image');
    } finally {
      setUploading(false);
    }
  };

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

  const hasChanges = () =>
    (Object.keys(initialForm) as (keyof FormState)[]).some(
      (k) => form[k] !== initialForm[k]
    );

  const handleCloseClick = () => {
    if (hasChanges()) setShowExitConfirm(true);
    else onOpenChange(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="blog-editor-overlay" />
        <Dialog.Content
          className="blog-editor-dialog"
          onOpenAutoFocus={(e) => e.preventDefault()}
          onCloseAutoFocus={(e) => e.preventDefault()}
        >

          <div className="blog-editor-header">
            <div>
              <span className="blog-editor-eyebrow">Article editor</span>
              <Dialog.Title className="blog-editor-title">
              {isEditMode ? 'Edit Article' : 'Create New Article'}
              </Dialog.Title>
            </div>
            <button type="button" onClick={handleCloseClick} className="blog-editor-close" aria-label="Close editor">
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

          {error && (
            <div className="blog-editor-error">
              {error}
            </div>
          )}

          <div className="blog-editor-body">

            <div className="blog-editor-field">
              <Label.Root htmlFor="title" className="blog-editor-label">Title *</Label.Root>
              <input
                id="title"
                type="text"
                value={form.title}
                onChange={(e) => set('title')(e.target.value)}
                placeholder="Enter article title..."
                className="blog-editor-input"
              />
            </div>

            <div className="blog-editor-field">
              <Label.Root htmlFor="subtitle" className="blog-editor-label">Subtitle</Label.Root>
              <input
                id="subtitle"
                type="text"
                value={form.subtitle}
                onChange={(e) => set('subtitle')(e.target.value)}
                placeholder="Enter subtitle (optional)..."
                className="blog-editor-input"
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

            <div className="blog-editor-field">
              <Label.Root htmlFor="tags" className="blog-editor-label">Tags</Label.Root>
              <input
                id="tags"
                type="text"
                value={form.tags}
                onChange={(e) => set('tags')(e.target.value)}
                placeholder="Enter tags separated by commas (e.g., tutorial, chess, beginner)"
                className="blog-editor-input"
              />
            </div>

            <div className="blog-editor-field">
              <Label.Root className="blog-editor-label">Content *</Label.Root>
              <RichTextEditor value={form.content} onChange={set('content')} />
            </div>

            <div className="blog-editor-footer">
              <ActionButton variant="secondary" onClick={() => handleSave('draft')} disabled={saving || uploading}>
                {saving ? 'Saving...' : 'Save Draft'}
              </ActionButton>
              <ActionButton variant="primary" onClick={() => handleSave('published')} disabled={saving || uploading}>
                {saving ? 'Publishing...' : 'Publish'}
              </ActionButton>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

const ActionButton: React.FC<{
  onClick: () => void;
  disabled: boolean;
  variant: 'primary' | 'secondary';
  children: React.ReactNode;
}> = ({ onClick, disabled, variant, children }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className={`blog-editor-action is-${variant}`}
  >
    {children}
  </button>
);

export default BlogEditor;
