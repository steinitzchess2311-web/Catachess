/**
 * CommentItem — YouTube-style comment with collapsible replies.
 *
 * Root comments show a "N replies ∨" toggle; children are hidden until
 * the user clicks it. Replies within the expanded section follow the
 * same pattern recursively.
 */
import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, HeartIcon, HeartFilledIcon } from '@radix-ui/react-icons';
import { CommentNode, Comment } from '../../../types/comment';
import { CommentInput, stringToColor } from './CommentInput';
import { commentApi } from '../../../utils/commentApi';

interface Props {
  node: CommentNode;
  currentUserId?: string;
  currentUserName?: string;
  isAdmin?: boolean;
  commentMap: Map<string, Comment>;
  onUpdate: () => void;
  /** Depth from root (0 = root comment) */
  depth?: number;
}

export const CommentItem: React.FC<Props> = ({
  node,
  currentUserId,
  currentUserName,
  isAdmin,
  commentMap,
  onUpdate,
  depth = 0,
}) => {
  const [showReplies, setShowReplies] = useState(false);
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [likeCount, setLikeCount] = useState(node.like_count);
  const [isLiked, setIsLiked] = useState(node.is_liked);
  const [liking, setLiking] = useState(false);

  const isOwn = !!currentUserId && currentUserId === node.author_id;
  const canAct = !!currentUserId;
  const hasReplies = node.children.length > 0;
  const quotedComment = node.quote_id ? commentMap.get(node.quote_id) : null;

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleLike = async () => {
    if (!canAct || liking) return;
    setLiking(true);
    const prevLiked = isLiked;
    const prevCount = likeCount;
    setIsLiked(!isLiked);
    setLikeCount(prev => isLiked ? Math.max(prev - 1, 0) : prev + 1);
    try {
      const res = await commentApi.toggleLike(node.id);
      setIsLiked(res.liked);
      setLikeCount(res.like_count);
    } catch {
      setIsLiked(prevLiked);
      setLikeCount(prevCount);
    } finally {
      setLiking(false);
    }
  };

  const handleReply = async (content: string) => {
    await commentApi.create(node.article_id, { content, parent_id: node.id });
    setShowReplyInput(false);
    setShowReplies(true); // auto-expand so the new reply is visible
    onUpdate();
  };

  const handleEdit = async (content: string) => {
    await commentApi.edit(node.id, content, node.version);
    setIsEditing(false);
    onUpdate();
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this comment?')) return;
    await commentApi.delete(node.id);
    onUpdate();
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="comment-item-wrap">
      <div className="comment-item">
        {/* Avatar */}
        <div
          className="comment-avatar sm"
          style={{ background: stringToColor(node.author_name) }}
        >
          {node.author_name.slice(0, 2).toUpperCase()}
        </div>

        <div className="comment-body">
          {/* Header */}
          <div className="comment-header">
            <span className="comment-author">@{node.author_name}</span>
            <span className="comment-date">{formatRelative(node.created_at)}</span>
            {node.edited && <span className="comment-edited-badge">(edited)</span>}
          </div>

          {/* Deleted placeholder */}
          {node.is_deleted ? (
            <p className="comment-deleted-text">[Comment removed]</p>
          ) : (
            <>
              {/* Quote */}
              {quotedComment && !quotedComment.is_deleted && (
                <div className="comment-quote">
                  <span className="comment-quote-author">@{quotedComment.author_name} </span>
                  {quotedComment.content.slice(0, 120)}{quotedComment.content.length > 120 ? '…' : ''}
                </div>
              )}

              {/* Content / edit mode */}
              {isEditing ? (
                <CommentInput
                  initialValue={node.content}
                  authorName={currentUserName}
                  isReply
                  autoFocus
                  onSubmit={handleEdit}
                  onCancel={() => setIsEditing(false)}
                />
              ) : (
                <p className="comment-content">{node.content}</p>
              )}

              {/* Actions */}
              {!isEditing && (
                <div className="comment-actions">
                  <button
                    className={`comment-action-btn like-btn ${isLiked ? 'liked' : ''}`}
                    onClick={handleLike}
                    disabled={liking || !canAct}
                    title={canAct ? 'Like' : 'Sign in to like'}
                  >
                    {isLiked
                      ? <HeartFilledIcon width={14} height={14} />
                      : <HeartIcon width={14} height={14} />
                    }
                    {likeCount > 0 && <span>{likeCount}</span>}
                  </button>

                  {canAct && (
                    <button
                      className="comment-action-btn reply-btn"
                      onClick={() => setShowReplyInput(v => !v)}
                    >
                      Reply
                    </button>
                  )}

                  {(isOwn || isAdmin) && (
                    <>
                      <button className="comment-action-btn" onClick={() => setIsEditing(true)}>
                        Edit
                      </button>
                      <button className="comment-action-btn delete" onClick={handleDelete}>
                        Delete
                      </button>
                    </>
                  )}
                </div>
              )}
            </>
          )}

          {/* Reply input — sits inside the comment body, below actions */}
          {showReplyInput && (
            <div style={{ marginTop: 10 }}>
              <CommentInput
                placeholder={`Reply to @${node.author_name}…`}
                authorName={currentUserName}
                isReply
                autoFocus
                onSubmit={handleReply}
                onCancel={() => setShowReplyInput(false)}
              />
            </div>
          )}

          {/* "N replies ∨" toggle — YouTube style */}
          {hasReplies && (
            <button
              className="replies-toggle"
              onClick={() => setShowReplies(v => !v)}
            >
              {showReplies
                ? <ChevronUpIcon width={14} height={14} />
                : <ChevronDownIcon width={14} height={14} />
              }
              {node.children.length} {node.children.length === 1 ? 'reply' : 'replies'}
            </button>
          )}
        </div>
      </div>

      {/* Expanded replies */}
      {showReplies && hasReplies && (
        <div className="comment-replies-section">
          {node.children.map(child => (
            <CommentItem
              key={child.id}
              node={child}
              currentUserId={currentUserId}
              currentUserName={currentUserName}
              isAdmin={isAdmin}
              commentMap={commentMap}
              onUpdate={onUpdate}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ── Util ─────────────────────────────────────────────────────────────────────

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;
  return `${Math.floor(months / 12)} year${Math.floor(months / 12) > 1 ? 's' : ''} ago`;
}
