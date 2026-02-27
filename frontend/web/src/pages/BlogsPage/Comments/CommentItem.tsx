/**
 * CommentItem — renders a single comment node and its nested children.
 * Recursive: children are rendered by calling CommentItem again.
 */
import React, { useState } from 'react';
import { HeartIcon, HeartFilledIcon } from '@radix-ui/react-icons';
import { CommentNode, Comment } from '../../../types/comment';
import { CommentInput, stringToColor } from './CommentInput';
import { commentApi } from '../../../utils/commentApi';

interface Props {
  node: CommentNode;
  currentUserId?: string;
  currentUserName?: string;
  isAdmin?: boolean;
  /** Parent flat map for resolving quote content */
  commentMap: Map<string, Comment>;
  onUpdate: () => void;   // refresh the whole list after any mutation
}

export const CommentItem: React.FC<Props> = ({
  node,
  currentUserId,
  currentUserName,
  isAdmin,
  commentMap,
  onUpdate,
}) => {
  const [showReply, setShowReply] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [likeCount, setLikeCount] = useState(node.like_count);
  const [isLiked, setIsLiked] = useState(node.is_liked);
  const [liking, setLiking] = useState(false);

  const isOwn = !!currentUserId && currentUserId === node.author_id;
  const canAct = !!currentUserId;
  const quotedComment = node.quote_id ? commentMap.get(node.quote_id) : null;

  const relativeTime = formatRelative(node.created_at);

  // ── Handlers ──────────────────────────────────────────────────────────────

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
    await commentApi.create(node.article_id, {
      content,
      parent_id: node.id,
    });
    setShowReply(false);
    onUpdate();
  };

  const handleEdit = async (content: string) => {
    await commentApi.edit(node.id, content, node.version);
    setIsEditing(false);
    onUpdate();
  };

  const handleDelete = async () => {
    if (!window.confirm('确认删除这条评论？')) return;
    await commentApi.delete(node.id);
    onUpdate();
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div>
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
            <span className="comment-author">{node.author_name}</span>
            <span className="comment-date">{relativeTime}</span>
            {node.edited && (
              <span className="comment-edited-badge">（已编辑）</span>
            )}
          </div>

          {/* Deleted placeholder */}
          {node.is_deleted ? (
            <p className="comment-deleted-text">该评论已被删除</p>
          ) : (
            <>
              {/* Quote block */}
              {quotedComment && !quotedComment.is_deleted && (
                <div className="comment-quote">
                  <div className="comment-quote-author">
                    @ {quotedComment.author_name}
                  </div>
                  <div>{quotedComment.content.slice(0, 120)}{quotedComment.content.length > 120 ? '…' : ''}</div>
                </div>
              )}

              {/* Edit mode */}
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
                  {/* Like */}
                  <button
                    className={`comment-action-btn ${isLiked ? 'liked' : ''}`}
                    onClick={handleLike}
                    disabled={liking || !canAct}
                    title={canAct ? '点赞' : '请先登录'}
                  >
                    {isLiked
                      ? <HeartFilledIcon width={13} height={13} />
                      : <HeartIcon width={13} height={13} />
                    }
                    {likeCount > 0 && <span>{likeCount}</span>}
                  </button>

                  {/* Reply */}
                  {canAct && (
                    <button
                      className="comment-action-btn"
                      onClick={() => setShowReply(v => !v)}
                    >
                      回复
                    </button>
                  )}

                  {/* Edit / Delete — own comment or admin */}
                  {(isOwn || isAdmin) && (
                    <>
                      <button
                        className="comment-action-btn"
                        onClick={() => setIsEditing(true)}
                      >
                        编辑
                      </button>
                      <button
                        className="comment-action-btn delete"
                        onClick={handleDelete}
                      >
                        删除
                      </button>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Inline reply input */}
      {showReply && (
        <div className="comment-reply-input">
          <CommentInput
            placeholder={`回复 ${node.author_name}…`}
            authorName={currentUserName}
            isReply
            autoFocus
            onSubmit={handleReply}
            onCancel={() => setShowReply(false)}
          />
        </div>
      )}

      {/* Nested children */}
      {node.children.length > 0 && (
        <div className="comment-children">
          {node.children.map(child => (
            <CommentItem
              key={child.id}
              node={child}
              currentUserId={currentUserId}
              currentUserName={currentUserName}
              isAdmin={isAdmin}
              commentMap={commentMap}
              onUpdate={onUpdate}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ── Util ───────────────────────────────────────────────────────────────────

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return `${mins} 分钟前`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} 小时前`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days} 天前`;
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}
