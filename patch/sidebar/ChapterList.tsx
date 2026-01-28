import React, { useEffect, useRef, useState } from 'react';

export interface ChapterListProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onRenameChapter: (chapterId: string, title: string) => Promise<void> | void;
}

export function ChapterList({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
  onRenameChapter,
}: ChapterListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState<string>('');
  const [savingId, setSavingId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  const startEditing = (chapterId: string, label: string) => {
    setEditingId(chapterId);
    setDraftTitle(label);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setDraftTitle('');
  };

  const commitEditing = async (chapterId: string, label: string) => {
    const nextTitle = draftTitle.trim();
    if (!nextTitle || nextTitle === label) {
      cancelEditing();
      return;
    }
    setSavingId(chapterId);
    try {
      await onRenameChapter(chapterId, nextTitle);
    } finally {
      setSavingId(null);
      cancelEditing();
    }
  };

  return (
    <section className="patch-chapter-list">
      <header className="patch-chapter-list__header">
        <div>
          <h3>Chapters</h3>
          <p>{chapters.length} total</p>
        </div>
        <button
          type="button"
          className="patch-chapter-list__new"
          onClick={onCreateChapter}
        >
          New Chapter
        </button>
      </header>
      <div className="patch-chapter-list__scroll">
        {chapters.length === 0 && (
          <div className="patch-chapter-list__empty">No chapters yet.</div>
        )}
        {chapters.map((chapter, index) => {
          const isActive = chapter.id === currentChapterId;
          const label = chapter.title || `Chapter ${index + 1}`;
          const order = typeof chapter.order === 'number' ? chapter.order + 1 : index + 1;
          const isEditing = editingId === chapter.id;
          const isSaving = savingId === chapter.id;
          return (
            <button
              key={chapter.id}
              type="button"
              className={`patch-chapter-list__item${isActive ? ' is-active' : ''}`}
              onClick={() => onSelectChapter(chapter.id)}
              disabled={isSaving}
            >
              <span className="patch-chapter-list__order">{order}</span>
              {isEditing ? (
                <input
                  ref={inputRef}
                  className="patch-chapter-list__title-input"
                  value={draftTitle}
                  onChange={(event) => setDraftTitle(event.target.value)}
                  onClick={(event) => event.stopPropagation()}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault();
                      commitEditing(chapter.id, label);
                    }
                    if (event.key === 'Escape') {
                      event.preventDefault();
                      cancelEditing();
                    }
                  }}
                  onBlur={() => commitEditing(chapter.id, label)}
                />
              ) : (
                <span
                  className="patch-chapter-list__title"
                  onDoubleClick={(event) => {
                    event.stopPropagation();
                    startEditing(chapter.id, label);
                  }}
                >
                  {label}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
