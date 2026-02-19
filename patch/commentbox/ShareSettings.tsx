import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStudy } from '../studyContext';
import { api } from '@ui/assets/api';

type VisibilityMode = 'public' | 'private' | 'shared';

interface UserResult { id: string; username: string; }
interface SharedUser { user_id: string; username: string; permission: string; }

const VIS = [
  { value: 'public'  as VisibilityMode, icon: '🌐', label: 'Public'     },
  { value: 'private' as VisibilityMode, icon: '🔒', label: 'Private'    },
  { value: 'shared'  as VisibilityMode, icon: '👥', label: 'Share with' },
];

export function ShareSettings() {
  const { state } = useStudy();

  const [visibility, setVisibility]       = useState<VisibilityMode>('private');
  const nodeVersionRef                     = useRef(1);
  const [visLoading, setVisLoading]       = useState(false);
  const [shareError, setShareError]       = useState<string | null>(null);
  const [sharedUsers, setSharedUsers]     = useState<SharedUser[]>([]);

  // Inline search state
  const [searchQuery, setSearchQuery]     = useState('');
  const [searchResults, setSearchResults] = useState<UserResult[]>([]);
  const [isSearching, setIsSearching]     = useState(false);
  const [searched, setSearched]           = useState(false);

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

  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setIsSearching(true); setSearched(true);
    try {
      const res = await api.get(`/api/v1/workspace/users/search?q=${encodeURIComponent(q)}`);
      setSearchResults((res as UserResult[]) || []);
    } catch {
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery]);

  const handleAddUser = useCallback(async (user: UserResult) => {
    if (!state.studyId) return;
    setSearchQuery(''); setSearchResults([]); setSearched(false); setShareError(null);
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

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <span style={sLabel}>Visibility</span>

      {/* Two independent containers side by side when shared */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>

        {/* ── Left container: visibility cards (static, never scrolls) ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0, width: isShared ? '50%' : '100%', transition: 'width 0.28s cubic-bezier(0.4,0,0.2,1)' }}>
          {VIS.map(({ value: v, icon, label }) => {
            const active = visibility === v;
            return (
              <button
                key={v} type="button"
                onClick={() => handleVisibilityChange(v)}
                disabled={visLoading}
                style={{
                  display: 'flex', alignItems: 'center', gap: '9px',
                  padding: '0 10px', height: '32px',
                  border: `1.5px solid ${active ? 'var(--accent, #4e7fff)' : 'var(--border, rgba(128,128,128,0.18))'}`,
                  borderRadius: '8px',
                  background: active ? 'var(--accent-bg, rgba(78,127,255,0.07))' : 'transparent',
                  cursor: visLoading ? 'default' : 'pointer',
                  transition: 'border-color 0.14s, background 0.14s',
                  opacity: visLoading && !active ? 0.5 : 1,
                  color: 'inherit', width: '100%', boxSizing: 'border-box',
                }}
              >
                <span style={{ fontSize: '15px', lineHeight: 1, flexShrink: 0 }}>{icon}</span>
                <span style={{ flex: 1, textAlign: 'left', fontSize: '12px', fontWeight: active ? 600 : 500, color: active ? 'var(--accent, #4e7fff)' : 'inherit' }}>
                  {label}
                </span>
                {active && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent, #4e7fff)', flexShrink: 0 }} />}
              </button>
            );
          })}
        </div>

        {/* ── Right container: access management (independent, scrollable) */}
        {isShared && (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column', gap: '5px',
            minWidth: 0,
            animation: 'fadeSlideIn 0.2s ease',
          }}>
            <span style={sLabel}>Who has access</span>

            {/* Scrollable user list — independent scroll container */}
            <div style={{
              overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px',
              maxHeight: '88px', flexShrink: 0,
            }}>
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
                      cursor: 'pointer', padding: 0, fontSize: '14px', lineHeight: 1,
                      color: 'var(--text-muted, #888)', opacity: 0.65, flexShrink: 0,
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    }}
                  >×</button>
                </div>
              ))}
            </div>

            {/* Inline search — plain input + Search button, always typeable */}
            <div style={{ display: 'flex', gap: '5px', alignItems: 'center', marginTop: '2px' }}>
              <div style={{
                flex: 1, display: 'flex', alignItems: 'center', gap: '6px',
                border: '1.5px solid var(--border, rgba(128,128,128,0.25))',
                borderRadius: '7px', padding: '0 8px', height: '28px',
                background: 'var(--surface, transparent)',
              }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted, #888)', flexShrink: 0 }}>🔍</span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => { setSearchQuery(e.target.value); setSearched(false); }}
                  onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
                  placeholder="Enter username..."
                  autoComplete="off"
                  style={{
                    flex: 1, border: 'none', outline: 'none',
                    background: 'transparent', color: 'inherit', fontSize: '11px',
                    minWidth: 0,
                  }}
                />
              </div>
              <button
                type="button"
                onClick={handleSearch}
                disabled={!searchQuery.trim() || isSearching}
                style={{
                  padding: '0 10px', height: '28px', flexShrink: 0,
                  border: 'none', borderRadius: '7px',
                  background: 'var(--accent, #4e7fff)', color: '#fff',
                  fontSize: '11px', fontWeight: 600, cursor: 'pointer',
                  opacity: (!searchQuery.trim() || isSearching) ? 0.5 : 1,
                  transition: 'opacity 0.14s',
                }}
              >
                {isSearching ? '···' : 'Search'}
              </button>
            </div>

            {/* Search results */}
            {searched && searchResults.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {searchResults.map(u => (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => handleAddUser(u)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '7px',
                      padding: '4px 7px', borderRadius: '6px',
                      border: '1px solid var(--border, rgba(128,128,128,0.12))',
                      background: 'none', cursor: 'pointer', color: 'inherit',
                      textAlign: 'left', width: '100%', fontSize: '11px',
                    }}
                  >
                    <div style={sAvatar('rgba(128,128,128,0.14)', 'var(--text-muted, #888)')}>
                      {(u.username || '?')[0].toUpperCase()}
                    </div>
                    <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {u.username}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--accent, #4e7fff)', flexShrink: 0 }}>+ Add</span>
                  </button>
                ))}
              </div>
            )}
            {searched && !isSearching && searchResults.length === 0 && (
              <span style={{ fontSize: '10px', color: 'var(--text-muted, #888)' }}>No users found</span>
            )}

            {shareError && (
              <span style={{ fontSize: '10px', color: 'var(--error, #e05252)' }}>{shareError}</span>
            )}
          </div>
        )}
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
