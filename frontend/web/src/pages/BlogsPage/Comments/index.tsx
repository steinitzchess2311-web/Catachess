/**
 * CommentSection — main entry point for article comments.
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

  const tree = useMemo(() => buildCommentTree(comments), [comments]);
  const commentMap = useMemo(() => new Map(comments.map(c => [c.id, c])), [comments]);

  const fetchComments = async () => {
    try {
      setError(null);
      const res = await commentApi.list(articleId);
      setComments(res.items);
      setTotal(res.total);
    } catch {
      setError('Failed to load comments. Please refresh.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchComments(); }, [articleId]);

  const handleRootComment = async (content: string) => {
    await commentApi.create(articleId, { content });
    await fetchComments();
  };

  return (
    <section className="comments-section">
      <h3 className="comments-title">
        {total > 0 ? `${total} Comment${total !== 1 ? 's' : ''}` : 'Comments'}
      </h3>

      {currentUserId ? (
        <CommentInput authorName={currentUserName} onSubmit={handleRootComment} />
      ) : (
        <div className="comments-login-hint">
          <a href="/login">Sign in</a> to join the discussion
        </div>
      )}

      {loading ? (
        <div className="comments-empty">Loading…</div>
      ) : error ? (
        <div className="comments-load-error">{error}</div>
      ) : tree.length === 0 ? (
        <div className="comments-empty">No comments yet. Be the first!</div>
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
