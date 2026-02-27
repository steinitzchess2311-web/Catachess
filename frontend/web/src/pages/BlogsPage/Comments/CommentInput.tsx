/**
 * CommentInput — textarea + submit/cancel buttons
 * Used for both root comments and nested replies.
 */
import React, { useState, useRef, useEffect } from 'react';

const MAX_LEN = 2000;

interface Props {
  placeholder?: string;
  initialValue?: string;
  authorName?: string;
  isReply?: boolean;
  autoFocus?: boolean;
  onSubmit: (content: string) => Promise<void>;
  onCancel?: () => void;
}

export const CommentInput: React.FC<Props> = ({
  placeholder = '写下你的评论…',
  initialValue = '',
  authorName,
  isReply = false,
  autoFocus = false,
  onSubmit,
  onCancel,
}) => {
  const [content, setContent] = useState(initialValue);
  const [submitting, setSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus) textareaRef.current?.focus();
  }, [autoFocus]);

  const handleSubmit = async () => {
    const trimmed = content.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await onSubmit(trimmed);
      setContent('');
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit();
    if (e.key === 'Escape' && onCancel) onCancel();
  };

  const initials = authorName
    ? authorName.slice(0, 2).toUpperCase()
    : '?';

  const charColor = content.length > MAX_LEN * 0.9 ? 'warn' : '';

  return (
    <div className="comment-input-wrap">
      <div className="comment-input-inner">
        {/* Avatar */}
        <div className={`comment-avatar ${isReply ? 'sm' : ''}`}
          style={{ background: stringToColor(authorName ?? 'X') }}>
          {initials}
        </div>

        <div className="comment-input-field-wrap">
          <textarea
            ref={textareaRef}
            className={`comment-textarea ${isReply ? 'reply' : ''}`}
            placeholder={placeholder}
            value={content}
            maxLength={MAX_LEN + 50}
            onChange={e => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="comment-input-footer">
            <span className={`comment-char-count ${charColor}`}>
              {content.length} / {MAX_LEN}
            </span>
            <div className="comment-input-actions">
              {onCancel && (
                <button className="btn-comment-cancel" onClick={onCancel}>
                  取消
                </button>
              )}
              <button
                className="btn-comment-submit"
                disabled={!content.trim() || content.length > MAX_LEN || submitting}
                onClick={handleSubmit}
              >
                {submitting ? '发送中…' : (isReply ? '回复' : '评论')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/** Deterministic pastel color from a string */
function stringToColor(str: string): string {
  const COLORS = [
    '#2563eb', '#7c3aed', '#db2777', '#059669',
    '#d97706', '#0891b2', '#4f46e5', '#be185d',
  ];
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return COLORS[Math.abs(hash) % COLORS.length];
}

export { stringToColor };
