import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStudy } from './studyContext';
import { api } from '@ui/assets/api';

type VisibilityMode = 'public' | 'private' | 'shared';

interface UserResult {
  id: string;
  username: string;
}

interface SharedUser {
  user_id: string;
  username: string;
  permission: string;
}

// ─── Visibility option config ──────────────────────────────────────────────
const VIS_OPTIONS: Array<{
  value: VisibilityMode;
  icon: string;
  label: string;
  desc: string;
}> = [
  { value: 'public',  icon: '🌐', label: 'Public',     desc: 'Anyone can view' },
  { value: 'private', icon: '🔒', label: 'Private',    desc: 'Only you'        },
  { value: 'shared',  icon: '👥', label: 'Share with', desc: 'Specific users'  },
];

// ─── Inline styles ─────────────────────────────────────────────────────────
const S = {
  settingsPanel: {
    padding: '14px 16px 10px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  label: {
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase' as const,
    color: 'var(--text-muted, #888)',
    marginBottom: '2px',
  },
  optionRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
  },
  optionBtn: (active: boolean, disabled: boolean): React.CSSProperties => ({
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    padding: '10px 6px 9px',
    border: active
      ? '1.5px solid var(--accent, #4e7fff)'
      : '1.5px solid var(--border, rgba(128,128,128,0.2))',
    borderRadius: '8px',
    background: active
      ? 'var(--accent-bg, rgba(78,127,255,0.08))'
      : 'var(--surface, transparent)',
    cursor: disabled ? 'default' : 'pointer',
    transition: 'border-color 0.15s, background 0.15s',
    opacity: disabled && !active ? 0.5 : 1,
  }),
  optionIcon: {
    fontSize: '18px',
    lineHeight: 1,
  },
  optionLabel: (active: boolean): React.CSSProperties => ({
    fontSize: '12px',
    fontWeight: active ? 600 : 500,
    color: active ? 'var(--accent, #4e7fff)' : 'var(--text, inherit)',
    lineHeight: 1,
  }),
  optionDesc: {
    fontSize: '10px',
    color: 'var(--text-muted, #888)',
    lineHeight: 1,
  },
  searchWrap: {
    position: 'relative' as const,
  },
  searchInput: {
    width: '100%',
    boxSizing: 'border-box' as const,
    padding: '8px 12px 8px 32px',
    border: '1.5px solid var(--border, rgba(128,128,128,0.25))',
    borderRadius: '7px',
    background: 'var(--input-bg, transparent)',
    color: 'inherit',
    fontSize: '13px',
    outline: 'none',
    transition: 'border-color 0.15s',
  },
  searchIcon: {
    position: 'absolute' as const,
    left: '10px',
    top: '50%',
    transform: 'translateY(-50%)',
    fontSize: '13px',
    pointerEvents: 'none' as const,
    color: 'var(--text-muted, #888)',
  },
  dropdown: {
    position: 'absolute' as const,
    top: 'calc(100% + 4px)',
    left: 0,
    right: 0,
    border: '1.5px solid var(--border, rgba(128,128,128,0.2))',
    borderRadius: '8px',
    background: 'var(--surface-elevated, var(--bg, #1a1a1a))',
    boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
    zIndex: 100,
    overflow: 'hidden',
  },
  dropdownItem: {
    display: 'block',
    width: '100%',
    padding: '9px 14px',
    textAlign: 'left' as const,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '13px',
    color: 'inherit',
    transition: 'background 0.1s',
  },
  chipsRow: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '6px',
    minHeight: '0px',
  },
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px',
    padding: '3px 8px 3px 10px',
    background: 'var(--accent-bg, rgba(78,127,255,0.1))',
    border: '1px solid var(--accent-border, rgba(78,127,255,0.3))',
    borderRadius: '100px',
    fontSize: '12px',
    color: 'var(--accent, #4e7fff)',
    fontWeight: 500,
  },
  chipRemove: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '14px',
    height: '14px',
    borderRadius: '50%',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    color: 'var(--accent, #4e7fff)',
    fontSize: '12px',
    padding: 0,
    lineHeight: 1,
    opacity: 0.7,
  },
  errorText: {
    fontSize: '12px',
    color: 'var(--error, #e05252)',
    marginTop: '-4px',
  },
};

// ─── Component ─────────────────────────────────────────────────────────────
export function CommentBox() {
  const { state, setComment } = useStudy();
  const currentNode = state.tree.nodes[state.cursorNodeId];
  const [value, setValue] = useState(currentNode?.comment || '');
  const [activeTab, setActiveTab] = useState<'comment' | 'output' | 'settings'>('comment');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');

  // Settings state
  const [visibility, setVisibility] = useState<VisibilityMode>('private');
  const nodeVersionRef = useRef(1);
  const [visibilityLoading, setVisibilityLoading] = useState(false);
  const [shareError, setShareError] = useState<string | null>(null);

  // Share-with state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);

  const fen = state.currentFen || '';

  // ── Load initial node state ──────────────────────────────────────────────
  useEffect(() => {
    if (!state.studyId) return;
    api.get(`/api/v1/workspace/nodes/${state.studyId}`)
      .then((node: any) => {
        if (node?.visibility) setVisibility(node.visibility as VisibilityMode);
        if (node?.version) nodeVersionRef.current = node.version;
      })
      .catch(() => {});
  }, [state.studyId]);

  // ── Load shared users when switching to share-with mode ──────────────────
  useEffect(() => {
    if (visibility !== 'shared' || !state.studyId) return;
    api.get(`/api/v1/workspace/share/${state.studyId}/users`)
      .then((data: any) => setSharedUsers(data as SharedUser[]))
      .catch(() => {});
  }, [visibility, state.studyId]);

  // ── Sync comment value when node changes ────────────────────────────────
  useEffect(() => {
    setValue(currentNode?.comment || '');
  }, [currentNode?.comment, state.cursorNodeId]);

  useEffect(() => {
    if (copyState === 'idle') return;
    const t = window.setTimeout(() => setCopyState('idle'), 1500);
    return () => window.clearTimeout(t);
  }, [copyState]);

  // ── User search with debounce ────────────────────────────────────────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = searchQuery.trim();
    if (!q) { setSearchResults([]); setShowDropdown(false); return; }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await api.get(
          `/api/v1/workspace/users/search?q=${encodeURIComponent(q)}`
        );
        setSearchResults(results as UserResult[]);
        setShowDropdown(true);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchQuery]);

  // ── Visibility change ────────────────────────────────────────────────────
  const handleVisibilityChange = useCallback(async (next: VisibilityMode) => {
    if (!state.studyId || visibilityLoading) return;
    setVisibilityLoading(true);
    setShareError(null);
    const prevVisibility = visibility;
    setVisibility(next); // optimistic
    try {
      await api.put(`/api/v1/workspace/nodes/${state.studyId}`, {
        visibility: next,
        version: nodeVersionRef.current,
      });
      nodeVersionRef.current += 1;
    } catch {
      setVisibility(prevVisibility); // revert
      setShareError('Failed to update visibility');
    } finally {
      setVisibilityLoading(false);
    }
  }, [state.studyId, visibility, visibilityLoading]);

  // ── Add user to share list ────────────────────────────────────────────────
  const handleAddUser = useCallback(async (user: UserResult) => {
    if (!state.studyId) return;
    setShowDropdown(false);
    setSearchQuery('');
    setShareError(null);
    // Optimistically add
    setSharedUsers(prev => {
      if (prev.some(u => u.user_id === user.id)) return prev;
      return [...prev, { user_id: user.id, username: user.username, permission: 'viewer' }];
    });
    try {
      await api.post(`/api/v1/workspace/share/${state.studyId}/users`, {
        user_id: user.id,
        permission: 'viewer',
        inherit_to_children: true,
      });
    } catch {
      setSharedUsers(prev => prev.filter(u => u.user_id !== user.id));
      setShareError('Failed to add user');
    }
  }, [state.studyId]);

  // ── Remove user from share list ──────────────────────────────────────────
  const handleRemoveUser = useCallback(async (userId: string) => {
    if (!state.studyId) return;
    setShareError(null);
    const prev = sharedUsers;
    setSharedUsers(p => p.filter(u => u.user_id !== userId));
    try {
      await api.delete(`/api/v1/workspace/share/${state.studyId}/users`, { user_id: userId });
    } catch {
      setSharedUsers(prev);
      setShareError('Failed to remove user');
    }
  }, [state.studyId, sharedUsers]);

  // ── Copy FEN ─────────────────────────────────────────────────────────────
  const handleCopyFen = async () => {
    if (!fen) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(fen);
      } else {
        const temp = document.createElement('textarea');
        temp.value = fen;
        temp.setAttribute('readonly', 'true');
        temp.style.position = 'absolute';
        temp.style.left = '-9999px';
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
      }
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };

  const downloadText = (filename: string, text: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExport = async (scope: 'study' | 'chapter') => {
    try {
      const studyId = state.studyId;
      const chapterId = state.chapterId;
      if (!studyId || (scope === 'chapter' && !chapterId)) return;
      const base = '/api/v1/workspace/studies/study-patch';
      const url = scope === 'study'
        ? `${base}/study/${studyId}/pgn-export`
        : `${base}/chapter/${chapterId}/pgn-export`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) throw new Error('Unexpected response format');
      const data = await response.json();
      if (!data?.success) throw new Error(data?.error || 'Export failed');
      downloadText(data.filename || `${studyId}-${scope}.pgn`, data.pgn || '');
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Export failed');
    }
  };

  // ─── Settings panel ────────────────────────────────────────────────────
  const renderSettings = () => (
    <div style={S.settingsPanel}>
      <div>
        <div style={S.label}>Visibility</div>
        <div style={S.optionRow}>
          {VIS_OPTIONS.map(({ value: v, icon, label, desc }) => {
            const active = visibility === v;
            return (
              <button
                key={v}
                type="button"
                style={S.optionBtn(active, visibilityLoading)}
                onClick={() => handleVisibilityChange(v)}
                disabled={visibilityLoading}
                title={desc}
              >
                <span style={S.optionIcon}>{icon}</span>
                <span style={S.optionLabel(active)}>{label}</span>
                <span style={S.optionDesc}>{desc}</span>
              </button>
            );
          })}
        </div>
      </div>

      {visibility === 'shared' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={S.searchWrap}>
            <span style={S.searchIcon}>⌕</span>
            <input
              ref={searchRef}
              type="text"
              placeholder="Search by username..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onFocus={() => { if (searchResults.length > 0) setShowDropdown(true); }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
              style={S.searchInput}
              autoComplete="off"
            />
            {isSearching && (
              <span style={{ ...S.searchIcon, left: 'auto', right: '10px', fontSize: '11px' }}>
                ···
              </span>
            )}
            {showDropdown && searchResults.length > 0 && (
              <div style={S.dropdown}>
                {searchResults.map(u => (
                  <button
                    key={u.id}
                    type="button"
                    style={S.dropdownItem}
                    onMouseDown={() => handleAddUser(u)}
                  >
                    {u.username}
                  </button>
                ))}
              </div>
            )}
            {showDropdown && !isSearching && searchResults.length === 0 && searchQuery.trim() && (
              <div style={{ ...S.dropdown, padding: '10px 14px', fontSize: '13px', color: 'var(--text-muted, #888)' }}>
                No users found
              </div>
            )}
          </div>

          {sharedUsers.length > 0 && (
            <div style={S.chipsRow}>
              {sharedUsers.map(u => (
                <span key={u.user_id} style={S.chip}>
                  {u.username}
                  <button
                    type="button"
                    style={S.chipRemove}
                    onClick={() => handleRemoveUser(u.user_id)}
                    title="Remove"
                    aria-label={`Remove ${u.username}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {shareError && <div style={S.errorText}>{shareError}</div>}
    </div>
  );

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="study-comment-box">
      <div className="study-comment-tabs">
        <button
          type="button"
          className={`study-comment-tab ${activeTab === 'comment' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('comment')}
        >
          Comment
        </button>
        <button
          type="button"
          className={`study-comment-tab ${activeTab === 'output' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('output')}
        >
          Output
        </button>
        <button
          type="button"
          className={`study-comment-tab ${activeTab === 'settings' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      <div className="study-comment-panel">
        {activeTab === 'settings' ? (
          renderSettings()
        ) : activeTab === 'comment' ? (
          <textarea
            className="study-comment-input"
            placeholder="Add comment..."
            value={value}
            onChange={(e) => {
              const next = e.target.value;
              setValue(next);
              if (state.cursorNodeId) setComment(state.cursorNodeId, next);
            }}
          />
        ) : (
          <div className="study-info-panel">
            <div className="study-fen-wrap">
              <textarea
                className="study-fen-box"
                readOnly
                value={fen || 'FEN unavailable'}
              />
              <button
                type="button"
                className="study-fen-button is-inline"
                onClick={handleCopyFen}
                disabled={!fen}
              >
                {copyState === 'copied' ? 'Copied' : copyState === 'error' ? 'Copy failed' : 'Copy FEN'}
              </button>
            </div>
            <div className="study-fen-actions">
              <button
                type="button"
                className="study-fen-button"
                onClick={() => handleExport('study')}
                disabled={!state.studyId}
              >
                Export Study PGN
              </button>
              <button
                type="button"
                className="study-fen-button"
                onClick={() => handleExport('chapter')}
                disabled={!state.studyId || !state.chapterId}
              >
                Export Chapter PGN
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CommentBox;
