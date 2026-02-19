import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStudy } from '../studyContext';
import { api } from '@ui/assets/api';

type VisibilityMode = 'public' | 'private' | 'shared';

interface UserResult  { id: string; username: string; }
interface SharedUser  { user_id: string; username: string; permission: string; }

const VIS = [
  { value: 'public'  as VisibilityMode, icon: '🌐', label: 'Public',     desc: 'Anyone can view' },
  { value: 'private' as VisibilityMode, icon: '🔒', label: 'Private',    desc: 'Only you'        },
  { value: 'shared'  as VisibilityMode, icon: '👥', label: 'Share with', desc: 'Specific users'  },
];

// ─── Add-user popover ────────────────────────────────────────────────────────
interface AddPopoverProps {
  inputRef: React.RefObject<HTMLInputElement>;
  query: string;
  setQuery: (q: string) => void;
  results: UserResult[];
  searching: boolean;
  onSelect: (u: UserResult) => void;
  onClose: () => void;
}

function AddPopover({ inputRef, query, setQuery, results, searching, onSelect, onClose }: AddPopoverProps) {
  // Close on outside click
  const wrapRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  return (
    <div
      ref={wrapRef}
      style={{
        position: 'absolute', bottom: 'calc(100% + 6px)', left: 0, right: 0,
        background: 'var(--surface-elevated, var(--bg, #1c1c1e))',
        border: '1.5px solid var(--border, rgba(128,128,128,0.18))',
        borderRadius: '10px',
        boxShadow: '0 12px 32px rgba(0,0,0,0.22)',
        overflow: 'hidden', zIndex: 200,
        minWidth: '180px',
      }}
    >
      {/* Search row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '9px 12px', borderBottom: '1px solid var(--border, rgba(128,128,128,0.12))' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-muted, #888)', flexShrink: 0 }}>🔍</span>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search users…"
          autoComplete="off"
          style={{
            flex: 1, border: 'none', outline: 'none', background: 'transparent',
            color: 'inherit', fontSize: '12px',
          }}
        />
        {searching && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted, #888)' }}>···</span>
        )}
      </div>

      {/* Results */}
      {results.length > 0 ? (
        <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
          {results.map(u => (
            <button
              key={u.id}
              type="button"
              onMouseDown={() => onSelect(u)}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                width: '100%', padding: '8px 12px',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'inherit', textAlign: 'left',
              }}
            >
              <span style={{
                width: '16px', height: '16px', borderRadius: '50%', flexShrink: 0,
                border: '1.5px solid var(--border, rgba(128,128,128,0.35))',
                display: 'inline-block',
              }} />
              <span style={{ fontSize: '13px' }}>{u.username}</span>
            </button>
          ))}
        </div>
      ) : query.trim() && !searching ? (
        <div style={{ padding: '10px 12px', fontSize: '12px', color: 'var(--text-muted, #888)' }}>
          No users found
        </div>
      ) : !query.trim() ? (
        <div style={{ padding: '10px 12px', fontSize: '12px', color: 'var(--text-muted, #888)' }}>
          Type to search…
        </div>
      ) : null}
    </div>
  );
}

// ─── Main settings component ─────────────────────────────────────────────────
export function ShareSettings() {
  const { state } = useStudy();

  const [visibility, setVisibility]         = useState<VisibilityMode>('private');
  const nodeVersionRef                       = useRef(1);
  const [visLoading, setVisLoading]         = useState(false);
  const [shareError, setShareError]         = useState<string | null>(null);
  const [sharedUsers, setSharedUsers]       = useState<SharedUser[]>([]);

  // Add-user popup
  const [addOpen, setAddOpen]               = useState(false);
  const [searchQuery, setSearchQuery]       = useState('');
  const [searchResults, setSearchResults]   = useState<UserResult[]>([]);
  const [isSearching, setIsSearching]       = useState(false);
  const debounceRef                         = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchInputRef                      = useRef<HTMLInputElement>(null);

  const isShared = visibility === 'shared';

  // ── Load node ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!state.studyId) return;
    api.get(`/api/v1/workspace/nodes/${state.studyId}`)
      .then((n: any) => {
        if (n?.visibility) setVisibility(n.visibility as VisibilityMode);
        if (n?.version)    nodeVersionRef.current = n.version;
      })
      .catch(() => {});
  }, [state.studyId]);

  // ── Load shared users ──────────────────────────────────────────────────────
  useEffect(() => {
    if (visibility !== 'shared' || !state.studyId) return;
    api.get(`/api/v1/workspace/share/${state.studyId}/users`)
      .then((d: any) => setSharedUsers(d as SharedUser[]))
      .catch(() => {});
  }, [visibility, state.studyId]);

  // ── Search debounce ────────────────────────────────────────────────────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = searchQuery.trim();
    if (!q) { setSearchResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.get(`/api/v1/workspace/users/search?q=${encodeURIComponent(q)}`);
        setSearchResults((res as UserResult[]) || []);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchQuery]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleVisibilityChange = useCallback(async (next: VisibilityMode) => {
    if (!state.studyId || visLoading) return;
    setVisLoading(true); setShareError(null);
    const prev = visibility; setVisibility(next);
    try {
      await api.put(`/api/v1/workspace/nodes/${state.studyId}`, {
        visibility: next, version: nodeVersionRef.current,
      });
      nodeVersionRef.current += 1;
    } catch {
      setVisibility(prev); setShareError('Failed to update visibility');
    } finally { setVisLoading(false); }
  }, [state.studyId, visibility, visLoading]);

  const handleAddUser = useCallback(async (user: UserResult) => {
    if (!state.studyId) return;
    setAddOpen(false); setSearchQuery(''); setSearchResults([]); setShareError(null);
    setSharedUsers(prev => prev.some(u => u.user_id === user.id)
      ? prev
      : [...prev, { user_id: user.id, username: user.username, permission: 'viewer' }]
    );
    try {
      await api.post(`/api/v1/workspace/share/${state.studyId}/users`, {
        user_id: user.id, permission: 'viewer', inherit_to_children: true,
      });
    } catch {
      setSharedUsers(prev => prev.filter(u => u.user_id !== user.id));
      setShareError('Failed to add user');
    }
  }, [state.studyId]);

  const handleRemoveUser = useCallback(async (userId: string) => {
    if (!state.studyId) return;
    const prev = sharedUsers;
    setSharedUsers(p => p.filter(u => u.user_id !== userId));
    try {
      await api.delete(`/api/v1/workspace/share/${state.studyId}/users`, { user_id: userId });
    } catch {
      setSharedUsers(prev); setShareError('Failed to remove user');
    }
  }, [state.studyId, sharedUsers]);

  const openAdd = useCallback(() => {
    setAddOpen(true);
    setTimeout(() => searchInputRef.current?.focus(), 40);
  }, []);

  const closeAdd = useCallback(() => {
    setAddOpen(false); setSearchQuery(''); setSearchResults([]);
  }, []);

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <span style={sLabel}>Visibility</span>

      {/* Animated split grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isShared ? '1fr 1fr' : '1fr',
        gap: isShared ? '10px' : '0',
        transition: 'grid-template-columns 0.28s cubic-bezier(0.4,0,0.2,1), gap 0.28s ease',
        overflow: 'hidden',
        alignItems: 'start',
      }}>

        {/* ── Left: vis selector ───────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {VIS.map(({ value: v, icon, label, desc }) => {
            const active = visibility === v;
            return (
              <button
                key={v} type="button"
                onClick={() => handleVisibilityChange(v)}
                disabled={visLoading}
                style={{
                  display: 'flex', alignItems: 'center', gap: '9px',
                  padding: '7px 10px',
                  border: `1.5px solid ${active ? 'var(--accent, #4e7fff)' : 'var(--border, rgba(128,128,128,0.18))'}`,
                  borderRadius: '8px',
                  background: active ? 'var(--accent-bg, rgba(78,127,255,0.07))' : 'transparent',
                  cursor: visLoading ? 'default' : 'pointer',
                  transition: 'border-color 0.14s, background 0.14s',
                  opacity: visLoading && !active ? 0.5 : 1,
                  color: 'inherit', width: '100%',
                }}
              >
                <span style={{ fontSize: '15px', lineHeight: 1, flexShrink: 0 }}>{icon}</span>
                <span style={{ flex: 1, textAlign: 'left' }}>
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: active ? 600 : 500, color: active ? 'var(--accent, #4e7fff)' : 'inherit', lineHeight: 1.2 }}>
                    {label}
                  </span>
                  {!isShared && (
                    <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted, #888)', lineHeight: 1.2, marginTop: '1px' }}>
                      {desc}
                    </span>
                  )}
                </span>
                {active && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent, #4e7fff)', flexShrink: 0 }} />}
              </button>
            );
          })}
        </div>

        {/* ── Right: access panel ──────────────────────────────────────── */}
        <div style={{
          display: 'flex', flexDirection: 'column', gap: '5px',
          overflow: 'hidden',
          opacity: isShared ? 1 : 0,
          transform: isShared ? 'translateX(0)' : 'translateX(8px)',
          transition: `opacity 0.2s ease ${isShared ? '0.16s' : '0s'}, transform 0.2s ease ${isShared ? '0.16s' : '0s'}`,
          pointerEvents: isShared ? 'auto' : 'none',
        }}>
          <span style={sLabel}>Who has access</span>

          {/* User list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', maxHeight: '116px', overflowY: 'auto' }}>
            {/* Owner */}
            <div style={sCard(true)}>
              <div style={sAvatar('#4e7fff', '#fff')}>Y</div>
              <span style={sName}>You</span>
              <span style={sBadge(true)}>Owner</span>
            </div>
            {sharedUsers.map(u => (
              <div key={u.user_id} style={sCard(false)}>
                <div style={sAvatar('rgba(128,128,128,0.14)', 'var(--text-muted, #888)')}>
                  {(u.username || '?')[0].toUpperCase()}
                </div>
                <span style={sName}>{u.username}</span>
                <span style={sBadge(false)}>{cap(u.permission || 'viewer')}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveUser(u.user_id)}
                  aria-label={`Remove ${u.username}`}
                  style={{
                    width: '14px', height: '14px', border: 'none', background: 'none',
                    cursor: 'pointer', padding: 0, lineHeight: 1,
                    fontSize: '14px', color: 'var(--text-muted, #888)', opacity: 0.65, flexShrink: 0,
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >×</button>
              </div>
            ))}
          </div>

          {/* Add user button + popover */}
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              onClick={openAdd}
              style={{
                display: 'flex', alignItems: 'center', gap: '5px',
                padding: '5px 9px',
                border: '1.5px dashed var(--border, rgba(128,128,128,0.28))',
                borderRadius: '7px', background: 'none', cursor: 'pointer',
                fontSize: '11px', color: 'var(--text-muted, #888)', width: '100%',
                transition: 'border-color 0.14s, color 0.14s',
              }}
            >
              <span style={{ fontSize: '14px', lineHeight: 1 }}>+</span>
              Add user
            </button>

            {addOpen && (
              <AddPopover
                inputRef={searchInputRef}
                query={searchQuery}
                setQuery={setSearchQuery}
                results={searchResults}
                searching={isSearching}
                onSelect={handleAddUser}
                onClose={closeAdd}
              />
            )}
          </div>

          {shareError && (
            <span style={{ fontSize: '10px', color: 'var(--error, #e05252)' }}>{shareError}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Micro-styles ─────────────────────────────────────────────────────────────
const sLabel: React.CSSProperties = {
  fontSize: '10px', fontWeight: 700, letterSpacing: '0.08em',
  textTransform: 'uppercase', color: 'var(--text-muted, #888)',
};
const sCard = (owner: boolean): React.CSSProperties => ({
  display: 'flex', alignItems: 'center', gap: '6px',
  padding: '5px 7px', borderRadius: '6px',
  background: owner ? 'var(--accent-bg, rgba(78,127,255,0.06))' : 'var(--surface-muted, rgba(128,128,128,0.04))',
  border: `1px solid ${owner ? 'rgba(78,127,255,0.16)' : 'var(--border, rgba(128,128,128,0.1))'}`,
});
const sAvatar = (bg: string, color: string): React.CSSProperties => ({
  width: '20px', height: '20px', borderRadius: '50%', flexShrink: 0,
  background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
  fontSize: '9px', fontWeight: 700, color,
});
const sName: React.CSSProperties = {
  flex: 1, fontSize: '11px', fontWeight: 500,
  minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
};
const sBadge = (owner: boolean): React.CSSProperties => ({
  fontSize: '9px', padding: '2px 5px', borderRadius: '100px', whiteSpace: 'nowrap',
  background: owner ? 'var(--accent-bg, rgba(78,127,255,0.1))' : 'rgba(128,128,128,0.08)',
  color: owner ? 'var(--accent, #4e7fff)' : 'var(--text-muted, #888)',
  fontWeight: 700,
});
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
