import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@ui/assets/api';

interface UserResult  { id: string; username: string; }
interface SharedUser  { user_id: string; username: string; permission: string; }
type SharePermission = 'viewer' | 'editor';

interface ShareWithProps {
  studyId: string;
}

export function ShareWith({ studyId }: ShareWithProps) {
  const [sharedUsers, setSharedUsers]     = useState<SharedUser[]>([]);
  const [shareError, setShareError]       = useState<string | null>(null);
  const [searchQuery, setSearchQuery]     = useState('');
  const [searchResults, setSearchResults] = useState<UserResult[]>([]);
  const [isSearching, setIsSearching]     = useState(false);
  const [searched, setSearched]           = useState(false);
  const [newPermission, setNewPermission] = useState<SharePermission>('viewer');

  // ── Load shared users ──────────────────────────────────────────────────────
  useEffect(() => {
    api.get(`/api/v1/workspace/share/${studyId}/users`)
      .then((d: any) => setSharedUsers(d as SharedUser[]))
      .catch(() => {});
  }, [studyId]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setIsSearching(true); setSearched(true);
    try {
      const res = await api.get(`/user/by-username/${encodeURIComponent(q)}`);
      setSearchResults(res ? [res as UserResult] : []);
    } catch {
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery]);

  const handleAddUser = useCallback(async (user: UserResult) => {
    setSearchQuery(''); setSearchResults([]); setSearched(false); setShareError(null);
    setSharedUsers(prev =>
      prev.some(u => u.user_id === user.id)
        ? prev
        : [...prev, { user_id: user.id, username: user.username, permission: newPermission }]
    );
    try {
      await api.post(`/api/v1/workspace/share/${studyId}/users`, {
        user_id: user.id, permission: newPermission, inherit_to_children: true,
      });
    } catch {
      setSharedUsers(prev => prev.filter(u => u.user_id !== user.id));
      setShareError('Failed to add user');
    }
  }, [studyId, newPermission]);

  const handleRoleChange = useCallback(async (userId: string, next: SharePermission) => {
    const prev = sharedUsers;
    setShareError(null);
    setSharedUsers(p => p.map(u => u.user_id === userId ? { ...u, permission: next } : u));
    try {
      await api.put(`/api/v1/workspace/share/${studyId}/users/role`, {
        user_id: userId,
        new_permission: next,
      });
    } catch {
      setSharedUsers(prev);
      setShareError('Failed to update access');
    }
  }, [studyId, sharedUsers]);

  const handleRemoveUser = useCallback(async (userId: string) => {
    const prev = sharedUsers;
    setSharedUsers(p => p.filter(u => u.user_id !== userId));
    try {
      await api.delete(`/api/v1/workspace/share/${studyId}/users`, { user_id: userId });
    } catch {
      setSharedUsers(prev); setShareError('Failed to remove user');
    }
  }, [studyId, sharedUsers]);

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', gap: '5px',
      minWidth: 0, animation: 'fadeSlideIn 0.2s ease',
    }}>
      <span style={sLabel}>Who has access</span>

      {/* Scrollable user list */}
      <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px', maxHeight: '88px' }}>
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
            <select
              value={normalizePermission(u.permission)}
              onChange={e => handleRoleChange(u.user_id, e.target.value as SharePermission)}
              aria-label={`Access for ${u.username}`}
              style={sSelect}
            >
              <option value="viewer">Can view</option>
              <option value="editor">Can edit</option>
            </select>
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

      {/* Inline search */}
      <div style={{ display: 'flex', gap: '4px' }}>
        {(['viewer', 'editor'] as SharePermission[]).map(permission => (
          <button
            key={permission}
            type="button"
            onClick={() => setNewPermission(permission)}
            style={sRoleButton(newPermission === permission)}
          >
            {permission === 'editor' ? 'Can edit' : 'Can view'}
          </button>
        ))}
      </div>

      {/* Inline search */}
      <div style={{ display: 'flex', gap: '5px', alignItems: 'center', marginTop: '2px' }}>
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', gap: '6px',
          border: '1.5px solid #d0d5dd',
          borderRadius: '7px', padding: '0 8px', height: '28px',
          background: '#fff',
        }}>
          <span style={{ fontSize: '11px', color: '#999', flexShrink: 0 }}>🔍</span>
          <input
            type="text"
            value={searchQuery}
            onChange={e => { setSearchQuery(e.target.value); setSearched(false); }}
            onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
            placeholder="Enter username..."
            autoComplete="off"
            style={{
              flex: 1, border: 'none', outline: 'none',
              background: 'transparent', color: '#111', fontSize: '11px',
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
const sSelect: React.CSSProperties = {
  border: '1px solid rgba(15, 23, 42, 0.12)',
  borderRadius: '6px',
  background: '#fff',
  color: '#1f2937',
  fontSize: '10px',
  fontWeight: 700,
  height: '24px',
  padding: '0 5px',
  flexShrink: 0,
};
const sRoleButton = (active: boolean): React.CSSProperties => ({
  flex: 1,
  border: `1px solid ${active ? '#2563eb' : 'rgba(15, 23, 42, 0.12)'}`,
  borderRadius: '6px',
  background: active ? 'rgba(37, 99, 235, 0.08)' : '#fff',
  color: active ? '#2563eb' : '#475569',
  fontSize: '10px',
  fontWeight: 800,
  height: '26px',
  cursor: 'pointer',
});
const normalizePermission = (permission: string): SharePermission => (
  permission === 'editor' || permission === 'admin' || permission === 'owner' ? 'editor' : 'viewer'
);
