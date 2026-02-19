import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStudy } from './studyContext';
import { api } from '@ui/assets/api';

type VisibilityMode = 'public' | 'private' | 'shared';

interface UserResult { id: string; username: string; }
interface SharedUser { user_id: string; username: string; permission: string; }

const VIS = [
  { value: 'public'  as VisibilityMode, icon: '🌐', label: 'Public',     desc: 'Anyone can view' },
  { value: 'private' as VisibilityMode, icon: '🔒', label: 'Private',    desc: 'Only you'        },
  { value: 'shared'  as VisibilityMode, icon: '👥', label: 'Share with', desc: 'Specific users'  },
];

// ─── Component ──────────────────────────────────────────────────────────────
export function CommentBox() {
  const { state, setComment } = useStudy();
  const currentNode = state.tree.nodes[state.cursorNodeId];

  // Tab / comment
  const [value, setValue] = useState(currentNode?.comment || '');
  const [activeTab, setActiveTab] = useState<'comment' | 'output' | 'settings'>('comment');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');

  // Visibility
  const [visibility, setVisibility] = useState<VisibilityMode>('private');
  const nodeVersionRef = useRef(1);
  const [visibilityLoading, setVisibilityLoading] = useState(false);
  const [shareError, setShareError] = useState<string | null>(null);

  // User search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);

  const fen = state.currentFen || '';

  // ── Load node visibility ─────────────────────────────────────────────────
  useEffect(() => {
    if (!state.studyId) return;
    api.get(`/api/v1/workspace/nodes/${state.studyId}`)
      .then((node: any) => {
        if (node?.visibility) setVisibility(node.visibility as VisibilityMode);
        if (node?.version)    nodeVersionRef.current = node.version;
      })
      .catch(() => {});
  }, [state.studyId]);

  // ── Load shared users when shared ────────────────────────────────────────
  useEffect(() => {
    if (visibility !== 'shared' || !state.studyId) return;
    api.get(`/api/v1/workspace/share/${state.studyId}/users`)
      .then((data: any) => setSharedUsers(data as SharedUser[]))
      .catch(() => {});
  }, [visibility, state.studyId]);

  // ── Sync comment ─────────────────────────────────────────────────────────
  useEffect(() => {
    setValue(currentNode?.comment || '');
  }, [currentNode?.comment, state.cursorNodeId]);

  useEffect(() => {
    if (copyState === 'idle') return;
    const t = window.setTimeout(() => setCopyState('idle'), 1500);
    return () => window.clearTimeout(t);
  }, [copyState]);

  // ── User search debounce ─────────────────────────────────────────────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = searchQuery.trim();
    if (!q) { setSearchResults([]); setShowDropdown(false); return; }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await api.get(`/api/v1/workspace/users/search?q=${encodeURIComponent(q)}`);
        setSearchResults((results as UserResult[]) || []);
        setShowDropdown(true);
      } catch {
        setSearchResults([]);
        setShowDropdown(false);
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
    const prev = visibility;
    setVisibility(next);
    try {
      await api.put(`/api/v1/workspace/nodes/${state.studyId}`, {
        visibility: next,
        version: nodeVersionRef.current,
      });
      nodeVersionRef.current += 1;
    } catch {
      setVisibility(prev);
      setShareError('Failed to update visibility');
    } finally {
      setVisibilityLoading(false);
    }
  }, [state.studyId, visibility, visibilityLoading]);

  // ── Add user ─────────────────────────────────────────────────────────────
  const handleAddUser = useCallback(async (user: UserResult) => {
    if (!state.studyId) return;
    setShowDropdown(false);
    setSearchQuery('');
    setShareError(null);
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

  // ── Remove user ──────────────────────────────────────────────────────────
  const handleRemoveUser = useCallback(async (userId: string) => {
    if (!state.studyId) return;
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
        const t = document.createElement('textarea');
        t.value = fen;
        t.style.position = 'absolute'; t.style.left = '-9999px';
        document.body.appendChild(t); t.select();
        document.execCommand('copy');
        document.body.removeChild(t);
      }
      setCopyState('copied');
    } catch { setCopyState('error'); }
  };

  const downloadText = (filename: string, text: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = filename;
    document.body.appendChild(link); link.click();
    document.body.removeChild(link); URL.revokeObjectURL(url);
  };

  const handleExport = async (scope: 'study' | 'chapter') => {
    try {
      const studyId   = state.studyId;
      const chapterId = state.chapterId;
      if (!studyId || (scope === 'chapter' && !chapterId)) return;
      const base = '/api/v1/workspace/studies/study-patch';
      const url  = scope === 'study'
        ? `${base}/study/${studyId}/pgn-export`
        : `${base}/chapter/${chapterId}/pgn-export`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);
      const data = await response.json();
      if (!data?.success) throw new Error(data?.error || 'Export failed');
      downloadText(data.filename || `${studyId}-${scope}.pgn`, data.pgn || '');
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Export failed');
    }
  };

  // ── Settings panel ────────────────────────────────────────────────────────
  const isShared = visibility === 'shared';

  const renderSettings = () => (
    <div style={{ padding: '12px 14px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const, color: 'var(--text-muted, #888)' }}>
        Visibility
      </div>

      {/* ── Animated split container ───────────────────────────────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isShared ? '1fr 1fr' : '1fr',
        gap: isShared ? '10px' : '0',
        transition: 'grid-template-columns 0.3s cubic-bezier(0.4,0,0.2,1), gap 0.3s ease',
        overflow: 'hidden',
        alignItems: 'start',
      }}>

        {/* ── Left: visibility cards ──────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {VIS.map(({ value: v, icon, label, desc }) => {
            const active = visibility === v;
            if (!isShared) {
              // Full vertical card
              return (
                <button
                  key={v} type="button"
                  onClick={() => handleVisibilityChange(v)}
                  disabled={visibilityLoading}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '9px 12px',
                    border: `1.5px solid ${active ? 'var(--accent, #4e7fff)' : 'var(--border, rgba(128,128,128,0.18))'}`,
                    borderRadius: '9px',
                    background: active ? 'var(--accent-bg, rgba(78,127,255,0.07))' : 'transparent',
                    cursor: visibilityLoading ? 'default' : 'pointer',
                    transition: 'border-color 0.15s, background 0.15s',
                    opacity: visibilityLoading && !active ? 0.55 : 1,
                    color: 'inherit',
                    textAlign: 'left' as const,
                  }}
                >
                  <span style={{ fontSize: '17px', lineHeight: 1, flexShrink: 0 }}>{icon}</span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: 'block', fontSize: '12px', fontWeight: active ? 600 : 500, color: active ? 'var(--accent, #4e7fff)' : 'inherit' }}>{label}</span>
                    <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted, #888)', marginTop: '1px' }}>{desc}</span>
                  </span>
                  {active && (
                    <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent, #4e7fff)', flexShrink: 0 }} />
                  )}
                </button>
              );
            }
            // Compact card when split
            return (
              <button
                key={v} type="button"
                onClick={() => handleVisibilityChange(v)}
                disabled={visibilityLoading}
                style={{
                  display: 'flex', alignItems: 'center', gap: '7px',
                  padding: '7px 9px',
                  border: `1.5px solid ${active ? 'var(--accent, #4e7fff)' : 'var(--border, rgba(128,128,128,0.18))'}`,
                  borderRadius: '8px',
                  background: active ? 'var(--accent-bg, rgba(78,127,255,0.07))' : 'transparent',
                  cursor: visibilityLoading ? 'default' : 'pointer',
                  transition: 'border-color 0.15s, background 0.15s',
                  color: 'inherit',
                  width: '100%',
                  textAlign: 'left' as const,
                }}
              >
                <span style={{ fontSize: '14px', lineHeight: 1, flexShrink: 0 }}>{icon}</span>
                <span style={{ flex: 1, fontSize: '11px', fontWeight: active ? 600 : 500, color: active ? 'var(--accent, #4e7fff)' : 'inherit' }}>
                  {label}
                </span>
                {active && (
                  <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent, #4e7fff)', flexShrink: 0 }} />
                )}
              </button>
            );
          })}
        </div>

        {/* ── Right: access panel (slides in) ─────────────────────────── */}
        <div style={{
          display: 'flex', flexDirection: 'column', gap: '6px',
          overflow: 'hidden',
          opacity: isShared ? 1 : 0,
          transform: isShared ? 'translateX(0)' : 'translateX(10px)',
          transition: `opacity 0.22s ease ${isShared ? '0.15s' : '0s'}, transform 0.22s ease ${isShared ? '0.15s' : '0s'}`,
          pointerEvents: isShared ? 'auto' : 'none',
        }}>
          <div style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const, color: 'var(--text-muted, #888)' }}>
            Who has access
          </div>

          {/* User list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '108px', overflowY: 'auto' as const }}>
            {/* Owner */}
            <div style={userCardStyle(true)}>
              <div style={avatarStyle('#4e7fff', '#fff')}>Y</div>
              <span style={nameStyle}>You</span>
              <span style={badgeStyle(true)}>Owner</span>
            </div>

            {/* Shared users */}
            {sharedUsers.map(u => (
              <div key={u.user_id} style={userCardStyle(false)}>
                <div style={avatarStyle('rgba(128,128,128,0.15)', 'var(--text-muted, #888)')}>
                  {(u.username || '?')[0].toUpperCase()}
                </div>
                <span style={nameStyle}>{u.username}</span>
                <span style={badgeStyle(false)}>{capitalise(u.permission || 'viewer')}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveUser(u.user_id)}
                  aria-label={`Remove ${u.username}`}
                  style={{
                    width: '15px', height: '15px', borderRadius: '50%',
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    border: 'none', background: 'none', cursor: 'pointer', padding: 0,
                    fontSize: '13px', lineHeight: 1, color: 'var(--text-muted, #888)',
                    opacity: 0.7, flexShrink: 0,
                  }}
                >×</button>
              </div>
            ))}
          </div>

          {/* Search */}
          <div style={{ position: 'relative' as const }}>
            <span style={{
              position: 'absolute' as const, left: '8px', top: '50%',
              transform: 'translateY(-50%)', fontSize: '12px',
              color: 'var(--text-muted, #888)', pointerEvents: 'none' as const,
            }}>⌕</span>
            <input
              ref={searchRef}
              type="text"
              placeholder="Add user…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onFocus={() => { if (searchResults.length > 0) setShowDropdown(true); }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 160)}
              autoComplete="off"
              style={{
                width: '100%', boxSizing: 'border-box' as const,
                padding: '6px 10px 6px 26px',
                border: '1.5px solid var(--border, rgba(128,128,128,0.2))',
                borderRadius: '7px',
                background: 'var(--input-bg, transparent)',
                color: 'inherit', fontSize: '11px', outline: 'none',
              }}
            />
            {isSearching && (
              <span style={{
                position: 'absolute' as const, right: '8px', top: '50%',
                transform: 'translateY(-50%)', fontSize: '10px', color: 'var(--text-muted, #888)',
              }}>···</span>
            )}

            {/* Dropdown */}
            {showDropdown && searchResults.length > 0 && (
              <div style={dropdownStyle}>
                {searchResults.map(u => (
                  <button
                    key={u.id}
                    type="button"
                    onMouseDown={() => handleAddUser(u)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '7px',
                      width: '100%', padding: '7px 10px',
                      textAlign: 'left' as const, background: 'none', border: 'none',
                      cursor: 'pointer', fontSize: '12px', color: 'inherit',
                    }}
                  >
                    <div style={avatarStyle('rgba(128,128,128,0.12)', 'var(--text-muted, #888)')}>
                      {u.username[0].toUpperCase()}
                    </div>
                    {u.username}
                  </button>
                ))}
              </div>
            )}
            {showDropdown && !isSearching && searchResults.length === 0 && searchQuery.trim() && (
              <div style={{ ...dropdownStyle, padding: '9px 12px', fontSize: '11px', color: 'var(--text-muted, #888)' }}>
                No users found
              </div>
            )}
          </div>

          {shareError && (
            <div style={{ fontSize: '10px', color: 'var(--error, #e05252)', marginTop: '-2px' }}>
              {shareError}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="study-comment-box">
      <div className="study-comment-tabs">
        {(['comment', 'output', 'settings'] as const).map(tab => (
          <button
            key={tab}
            type="button"
            className={`study-comment-tab ${activeTab === tab ? 'is-active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'comment' ? 'Comment' : tab === 'output' ? 'Output' : 'Settings'}
          </button>
        ))}
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
              <button type="button" className="study-fen-button" onClick={() => handleExport('study')}   disabled={!state.studyId}>Export Study PGN</button>
              <button type="button" className="study-fen-button" onClick={() => handleExport('chapter')} disabled={!state.studyId || !state.chapterId}>Export Chapter PGN</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Shared micro-styles ──────────────────────────────────────────────────────
const userCardStyle = (isOwner: boolean): React.CSSProperties => ({
  display: 'flex', alignItems: 'center', gap: '6px',
  padding: '5px 7px', borderRadius: '7px',
  background: isOwner ? 'var(--accent-bg, rgba(78,127,255,0.06))' : 'var(--surface-muted, rgba(128,128,128,0.04))',
  border: `1px solid ${isOwner ? 'var(--accent-border, rgba(78,127,255,0.18))' : 'var(--border, rgba(128,128,128,0.1))'}`,
});

const avatarStyle = (bg: string, color: string): React.CSSProperties => ({
  width: '20px', height: '20px', borderRadius: '50%', flexShrink: 0,
  background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
  fontSize: '9px', fontWeight: 700, color,
});

const nameStyle: React.CSSProperties = {
  flex: 1, fontSize: '11px', fontWeight: 500,
  minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
};

const badgeStyle = (isOwner: boolean): React.CSSProperties => ({
  fontSize: '9px', padding: '2px 5px', borderRadius: '100px', whiteSpace: 'nowrap',
  background: isOwner ? 'var(--accent-bg, rgba(78,127,255,0.1))' : 'rgba(128,128,128,0.08)',
  color: isOwner ? 'var(--accent, #4e7fff)' : 'var(--text-muted, #888)',
  fontWeight: 700, letterSpacing: '0.04em',
});

const dropdownStyle: React.CSSProperties = {
  position: 'absolute', top: 'calc(100% + 3px)', left: 0, right: 0,
  border: '1.5px solid var(--border, rgba(128,128,128,0.18))',
  borderRadius: '8px',
  background: 'var(--surface-elevated, var(--bg, #1a1a1a))',
  boxShadow: '0 8px 20px rgba(0,0,0,0.18)',
  zIndex: 100, overflow: 'hidden',
};

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export default CommentBox;
