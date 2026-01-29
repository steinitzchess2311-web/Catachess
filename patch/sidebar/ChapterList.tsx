import React, { useEffect, useRef, useState } from 'react';

export interface ChapterListProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onRenameChapter: (chapterId: string, title: string) => Promise<void> | void;
  onDeleteChapter: (chapterId: string) => Promise<void> | void;
}

export function ChapterList({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
  onRenameChapter,
  onDeleteChapter,
}: ChapterListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState<string>('');
  const [savingId, setSavingId] = useState<string | null>(null);
  const [errorId, setErrorId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; label: string } | null>(null);
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
    setErrorId(null);
  };

  const commitEditing = async (chapterId: string, label: string) => {
    const nextTitle = draftTitle.trim();
    if (nextTitle.includes('/')) {
      setErrorId(chapterId);
      return;
    }
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

  const handleDelete = (chapterId: string, label: string) => {
    setConfirmDelete({ id: chapterId, label });
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
                <div className="patch-chapter-list__title-edit">
                  <input
                    ref={inputRef}
                    className="patch-chapter-list__title-input"
                    value={draftTitle}
                    onChange={(event) => {
                      const nextValue = event.target.value;
                      setDraftTitle(nextValue);
                      if (!nextValue.includes('/')) {
                        setErrorId(null);
                      }
                    }}
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
                  {errorId === chapter.id && (
                    <span className="patch-chapter-list__error">No "/" in study or folder name</span>
                  )}
                </div>
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
              <button
                type="button"
                className="patch-chapter-list__delete"
                onClick={(event) => {
                  event.stopPropagation();
                  handleDelete(chapter.id, label);
                }}
                aria-label={`Delete ${label}`}
                title="Delete chapter"
                disabled={isSaving}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9z" />
                </svg>
              </button>
            </button>
          );
        })}
      </div>
      {confirmDelete && (
        <div className="patch-action-overlay" role="dialog" aria-modal="true">
          <div className="patch-action-card">
            <div className="patch-action-title">Delete Chapter</div>
            <div className="patch-action-body">
              <div>Are you sure you want to delete</div>
              <div className="patch-action-emphasis">{confirmDelete.label}?</div>
            </div>
            <div className="patch-action-buttons">
              <button
                type="button"
                className="patch-action-btn"
                onClick={() => setConfirmDelete(null)}
              >
                No
              </button>
              <button
                type="button"
                className="patch-action-btn is-danger"
                onClick={async () => {
                  await onDeleteChapter(confirmDelete.id);
                  setConfirmDelete(null);
                }}
              >
                Yes
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
