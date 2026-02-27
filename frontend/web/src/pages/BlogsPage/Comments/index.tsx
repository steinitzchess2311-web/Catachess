/**
 * CommentSection — main entry point for article comments.
 *
 * Responsibilities:
 *   1. Fetch flat comment list from API
 *   2. Build tree via buildCommentTree()
 *   3. Render login hint / root CommentInput / tree of CommentItems
 */
import React, { useEffect, useMemo, useState } from 'react';
import { commentApi } from '../../../utils/commentApi';
import { Comment } from '../../../types/comment';
import { buildCommentTree } from './commentTree';
import { CommentInput } from './CommentInput';
import { CommentItem } from './CommentItem';
import './Comments.css';

interface Props {
  articleId: string;
  currentUserId?: string;
  currentUserName?: string;
  isAdmin?: boolean;
}

const CommentSection: React.FC<Props> = ({
  articleId,
  currentUserId,
  currentUserName,
  isAdmin,
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build tree & comment map on every fetch
  const tree = useMemo(() => buildCommentTree(comments), [comments]);
  const commentMap = useMemo(
    () => new Map(comments.map(c => [c.id, c])),
    [comments],
  );

  const fetchComments = async () => {
    try {
      setError(null);
      const res = await commentApi.list(articleId);
      setComments(res.items);
      setTotal(res.total);
    } catch {
      setError('加载评论失败，请刷新重试。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [articleId]);

  const handleRootComment = async (content: string) => {
    await commentApi.create(articleId, { content });
    await fetchComments();
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <section className="comments-section">
      <h3 className="comments-title">
        评论{total > 0 ? ` (${total})` : ''}
      </h3>

      {/* Root comment input */}
      {currentUserId ? (
        <CommentInput
          authorName={currentUserName}
          onSubmit={handleRootComment}
        />
      ) : (
        <div className="comments-login-hint">
          <a href="/login">登录</a>后参与讨论
        </div>
      )}

      {/* Comment list */}
      {loading ? (
        <div className="comments-empty">加载中…</div>
      ) : error ? (
        <div className="comments-load-error">{error}</div>
      ) : tree.length === 0 ? (
        <div className="comments-empty">暂无评论，来说第一句吧 👋</div>
      ) : (
        <div className="comment-thread">
          {tree.map(node => (
            <CommentItem
              key={node.id}
              node={node}
              currentUserId={currentUserId}
              currentUserName={currentUserName}
              isAdmin={isAdmin}
              commentMap={commentMap}
              onUpdate={fetchComments}
            />
          ))}
        </div>
      )}
    </section>
  );
};

export default CommentSection;
