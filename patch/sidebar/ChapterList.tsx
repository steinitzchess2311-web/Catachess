import React, { useEffect, useRef, useState } from 'react';

export interface ChapterListProps {
  chapters: Array<{ id: string; title?: string; order?: number }>;
  currentChapterId: string | null;
  onSelectChapter: (chapterId: string) => void;
  onCreateChapter: () => void;
  onRenameChapter: (chapterId: string, title: string) => Promise<void> | void;
  onDeleteChapter: (chapterId: string) => Promise<void> | void;
  onReorderChapters: (
    order: string[],
    context: { draggedId: string; targetId: string; placement: 'before' | 'after' }
  ) => Promise<void> | void;
}

export function ChapterList({
  chapters,
  currentChapterId,
  onSelectChapter,
  onCreateChapter,
  onRenameChapter,
  onDeleteChapter,
  onReorderChapters,
}: ChapterListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState<string>('');
  const [savingId, setSavingId] = useState<string | null>(null);
  const [errorId, setErrorId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; label: string } | null>(null);
  const [confirmReorder, setConfirmReorder] = useState<{
    draggedId: string;
    targetId: string;
    placement: 'before' | 'after';
    order: string[];
  } | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<{ id: string; placement: 'before' | 'after' } | null>(null);
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
    if (chapters.length <= 1) return;
    setConfirmDelete({ id: chapterId, label });
  };

  const resolveLabel = (chapter: { id: string; title?: string; order?: number }, index: number) => {
    const orderValue = typeof chapter.order === 'number' ? chapter.order + 1 : index + 1;
    return chapter.title || `Chapter ${orderValue}`;
  };
  const labelMap = new Map(
    chapters.map((chapter, index) => [chapter.id, resolveLabel(chapter, index)])
  );
  const getLabel = (chapterId: string, fallback: string) => {
    return labelMap.get(chapterId) || fallback;
  };

  const computeReorder = (
    draggedId: string,
    targetId: string,
    placement: 'before' | 'after'
  ): string[] | null => {
    if (draggedId === targetId) return null;
    const ids = chapters.map((chapter) => chapter.id);
    if (!ids.includes(draggedId) || !ids.includes(targetId)) return null;
    const next = ids.filter((id) => id !== draggedId);
    const targetIndex = next.indexOf(targetId);
    const insertIndex = placement === 'after' ? targetIndex + 1 : targetIndex;
    next.splice(insertIndex, 0, draggedId);
    return next;
  };

  const handleDragStart = (event: React.DragEvent<HTMLSpanElement>, chapterId: string) => {
    if (editingId === chapterId || savingId === chapterId) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', chapterId);
    setDraggingId(chapterId);
  };

  const handleDragEnd = () => {
    setDraggingId(null);
    setDropTarget(null);
  };

  const handleDragOver = (
    event: React.DragEvent<HTMLButtonElement>,
    chapterId: string
  ) => {
    if (!draggingId || draggingId === chapterId) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    const rect = event.currentTarget.getBoundingClientRect();
    const mid = rect.top + rect.height / 2;
    const placement: 'before' | 'after' = event.clientY < mid ? 'before' : 'after';
    setDropTarget({ id: chapterId, placement });
  };

  const handleDropOnList = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!draggingId || !dropTarget || draggingId === dropTarget.id) {
      setDropTarget(null);
      setDraggingId(null);
      return;
    }
    const placement = dropTarget.placement;
    const order = computeReorder(draggingId, dropTarget.id, placement);
    setDropTarget(null);
    setDraggingId(null);
    if (!order) return;
    setConfirmReorder({
      draggedId: draggingId,
      targetId: dropTarget.id,
      placement,
      order,
    });
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
      <div
        className="patch-chapter-list__scroll"
        onDragOver={(event) => {
          if (!draggingId) return;
          event.preventDefault();
          event.dataTransfer.dropEffect = 'move';
        }}
        onDrop={handleDropOnList}
      >
        {chapters.length === 0 && (
          <div className="patch-chapter-list__empty">No chapters yet.</div>
        )}
        {chapters.map((chapter, index) => {
          const canDelete = chapters.length > 1;
          const isActive = chapter.id === currentChapterId;
          const orderValue = typeof chapter.order === 'number' ? chapter.order + 1 : index + 1;
          const label = resolveLabel(chapter, index);
          const order = orderValue;
          const isEditing = editingId === chapter.id;
          const isSaving = savingId === chapter.id;
          const isDragging = draggingId === chapter.id;
          const isDropBefore = dropTarget?.id === chapter.id && dropTarget.placement === 'before';
          const isDropAfter = dropTarget?.id === chapter.id && dropTarget.placement === 'after';
          return (
            <button
              key={chapter.id}
              type="button"
              className={[
                'patch-chapter-list__item',
                isActive ? 'is-active' : '',
                isDragging ? 'is-dragging' : '',
                isDropBefore ? 'is-drop-before' : '',
                isDropAfter ? 'is-drop-after' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => onSelectChapter(chapter.id)}
              disabled={isSaving}
              onDragOver={(event) => handleDragOver(event, chapter.id)}
            >
              <span
                className="patch-chapter-list__order"
                draggable={!isEditing && !isSaving}
                onDragStart={(event) => handleDragStart(event, chapter.id)}
                onDragEnd={handleDragEnd}
                onClick={(event) => event.stopPropagation()}
                role="button"
                tabIndex={0}
                aria-label={`Reorder ${label}`}
              >
                {order}
              </span>
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
              {canDelete && (
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
              )}
            </button>
          );
        })}
      </div>
      {confirmDelete && (
        <div className="patch-action-overlay" role="dialog" aria-modal="true">
          <div className="patch-action-card">
            <div className="patch-action-title">Delete Chapter</div>
            <div className="patch-action-body">
              <div>Are you sure you want to delete the chapter</div>
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
      {confirmReorder && (
        <div className="patch-action-overlay" role="dialog" aria-modal="true">
          <div className="patch-action-card">
            <div className="patch-action-title">Confirm Move</div>
            <div className="patch-action-body">
              <div>
                Move
                <span className="patch-action-emphasis">
                  {' '}
                  {getLabel(confirmReorder.draggedId, 'this chapter')}
                </span>
                {confirmReorder.placement === 'after' ? ' after ' : ' before '}
                <span className="patch-action-emphasis">
                  {getLabel(confirmReorder.targetId, 'this chapter')}
                </span>
                ?
              </div>
            </div>
            <div className="patch-action-buttons">
              <button
                type="button"
                className="patch-action-btn"
                onClick={() => setConfirmReorder(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-action-btn"
                onClick={async () => {
                  await onReorderChapters(confirmReorder.order, {
                    draggedId: confirmReorder.draggedId,
                    targetId: confirmReorder.targetId,
                    placement: confirmReorder.placement,
                  });
                  setConfirmReorder(null);
                }}
              >
                Move
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
