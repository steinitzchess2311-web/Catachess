import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Cross2Icon,
  DotFilledIcon,
  FileTextIcon,
  GlobeIcon,
  LockClosedIcon,
  MagnifyingGlassIcon,
  PersonIcon,
  Share2Icon,
} from '@radix-ui/react-icons';
import { api } from '@ui/assets/api';
import './Dialog.css';
import './NodeShareModal.css';

type VisMode = 'public' | 'private' | 'shared';

interface UserResult  { id: string; username: string; }
interface SharedUser  { user_id: string; username: string; permission: string; }

interface NodeShareModalProps {
  node: { id: string; title: string; node_type: 'folder' | 'study'; version: number; };
  onClose: () => void;
}

const VIS: { value: VisMode; icon: React.ReactNode; label: string }[] = [
  { value: 'public',  icon: <GlobeIcon width="18" height="18" />, label: 'Public' },
  { value: 'private', icon: <LockClosedIcon width="18" height="18" />, label: 'Private' },
  { value: 'shared',  icon: <Share2Icon width="18" height="18" />, label: 'Shared' },
];

const CASCADE_HINT: Record<VisMode, string | null> = {
  public:  'All content inside this folder will be made public.',
  private: 'This folder and all its content will be hidden from public view.',
  shared:  null,
};

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

const NodeShareModal: React.FC<NodeShareModalProps> = ({ node, onClose }) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  // ── Visibility ──────────────────────────────────────────────────────────────
  const [visibility, setVisibility] = useState<VisMode>('private');
  const [visLoading, setVisLoading] = useState(false);
  const [visError,   setVisError]   = useState<string | null>(null);
  const versionRef = useRef(node.version);

  useEffect(() => {
    api.get(`/api/v1/workspace/nodes/${node.id}`)
      .then((n: any) => {
        if (n?.visibility) setVisibility(n.visibility as VisMode);
        if (n?.version)    versionRef.current = n.version;
      })
      .catch(() => {});
  }, [node.id]);

  const handleVisChange = useCallback(async (next: VisMode) => {
    if (visLoading || next === visibility) return;
    setVisLoading(true); setVisError(null);
    const prev = visibility; setVisibility(next);
    try {
      await api.put(`/api/v1/workspace/nodes/${node.id}`, {
        visibility: next, version: versionRef.current,
      });
      versionRef.current += 1;
    } catch {
      setVisibility(prev); setVisError('Failed to update visibility');
    } finally { setVisLoading(false); }
  }, [node.id, visibility, visLoading]);

  // ── Share-with ──────────────────────────────────────────────────────────────
  const [sharedUsers,    setSharedUsers]    = useState<SharedUser[]>([]);
  const [searchQuery,    setSearchQuery]    = useState('');
  const [searchResults,  setSearchResults]  = useState<UserResult[]>([]);
  const [isSearching,    setIsSearching]    = useState(false);
  const [searched,       setSearched]       = useState(false);
  const [shareError,     setShareError]     = useState<string | null>(null);

  useEffect(() => {
    api.get(`/api/v1/workspace/share/${node.id}/users`)
      .then((d: any) => setSharedUsers(d as SharedUser[]))
      .catch(() => {});
  }, [node.id]);

  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setIsSearching(true); setSearched(true);
    try {
      const res = await api.get(`/user/by-username/${encodeURIComponent(q)}`);
      setSearchResults(res ? [res as UserResult] : []);
    } catch { setSearchResults([]); }
    finally  { setIsSearching(false); }
  }, [searchQuery]);

  const handleAddUser = useCallback(async (user: UserResult) => {
    setSearchQuery(''); setSearchResults([]); setSearched(false); setShareError(null);
    setSharedUsers(prev =>
      prev.some(u => u.user_id === user.id)
        ? prev
        : [...prev, { user_id: user.id, username: user.username, permission: 'viewer' }]
    );
    try {
      await api.post(`/api/v1/workspace/share/${node.id}/users`, {
        user_id: user.id, permission: 'viewer', inherit_to_children: true,
      });
    } catch {
      setSharedUsers(prev => prev.filter(u => u.user_id !== user.id));
      setShareError('Failed to add user');
    }
  }, [node.id]);

  const handleRemoveUser = useCallback(async (userId: string) => {
    const snap = sharedUsers;
    setSharedUsers(p => p.filter(u => u.user_id !== userId));
    try {
      await api.delete(`/api/v1/workspace/share/${node.id}/users`, { user_id: userId });
    } catch {
      setSharedUsers(snap); setShareError('Failed to remove user');
    }
  }, [node.id, sharedUsers]);

  // ── Keyboard / overlay close ────────────────────────────────────────────────
  useEffect(() => {
    const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', fn);
    return () => document.removeEventListener('keydown', fn);
  }, [onClose]);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  const isShared = visibility === 'shared';
  const renderNodeIcon = () => {
    if (node.node_type === 'folder') {
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
        </svg>
      );
    }
    return <FileTextIcon width="18" height="18" aria-hidden="true" />;
  };

  return (
    <div ref={overlayRef} className="cc-dialog-overlay nsm-overlay" onClick={handleOverlayClick}>
      <div className="cc-dialog-card cc-dialog-card--wide nsm-card" role="dialog" aria-modal="true" aria-label={`Share "${node.title}"`}>

        {/* Header */}
        <div className="cc-dialog-header nsm-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon">{renderNodeIcon()}</span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Share</p>
              <h3 className="cc-dialog-title">{node.title}</h3>
              <p className="cc-dialog-subtitle">{node.node_type === 'folder' ? 'Folder' : 'Study'} access settings</p>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body nsm-body">

          {/* Visibility section */}
          <span className="nsm-section-label">Visibility</span>
          <div className="nsm-vis-grid">
            {VIS.map(({ value, icon, label }) => {
              const active = visibility === value;
              return (
                <button
                  key={value}
                  type="button"
                  className={`nsm-vis-card${active ? ' is-active' : ''}`}
                  onClick={() => handleVisChange(value)}
                  disabled={visLoading}
                >
                  {active && <DotFilledIcon className="nsm-vis-dot" width="16" height="16" aria-hidden="true" />}
                  <span className="nsm-vis-icon">{icon}</span>
                  <span className="nsm-vis-label">{label}</span>
                </button>
              );
            })}
          </div>
          {visError && <span className="nsm-error">{visError}</span>}
          {node.node_type === 'folder' && CASCADE_HINT[visibility] && (
            <span className="nsm-cascade-hint">{CASCADE_HINT[visibility]}</span>
          )}

          {/* Share-with panel — animated in */}
          {isShared && (
            <div className="nsm-share-panel">
              <span className="nsm-section-label">Who has access</span>

              {/* User list */}
              <div className="nsm-user-list">
                <div className="nsm-user-row nsm-user-row--owner">
                  <div className="nsm-avatar nsm-avatar--owner"><PersonIcon width="14" height="14" aria-hidden="true" /></div>
                  <span className="nsm-user-name">You</span>
                  <span className="nsm-badge nsm-badge--owner">Owner</span>
                </div>
                {sharedUsers.map(u => (
                  <div key={u.user_id} className="nsm-user-row">
                    <div className="nsm-avatar">{(u.username || '?')[0].toUpperCase()}</div>
                    <span className="nsm-user-name">{u.username}</span>
                    <span className="nsm-badge">{cap(u.permission || 'viewer')}</span>
                    <button
                      type="button"
                      className="nsm-remove-btn"
                      onClick={() => handleRemoveUser(u.user_id)}
                      aria-label={`Remove ${u.username}`}
                    >×</button>
                  </div>
                ))}
              </div>

              {/* Search */}
              <div className="nsm-search-row">
                <div className="nsm-search-input-wrap">
                  <MagnifyingGlassIcon className="nsm-search-icon" width="16" height="16" aria-hidden="true" />
                  <input
                    type="text"
                    className="cc-dialog-input nsm-search-input"
                    placeholder="Search username"
                    value={searchQuery}
                    autoComplete="off"
                    onChange={e => { setSearchQuery(e.target.value); setSearched(false); }}
                    onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
                  />
                </div>
                <button
                  type="button"
                  className="cc-dialog-button cc-dialog-button--primary nsm-search-btn"
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isSearching}
                >{isSearching ? '···' : 'Search'}</button>
              </div>

              {/* Results */}
              {searched && searchResults.length > 0 && (
                <div className="nsm-results">
                  {searchResults.map(u => (
                    <button
                      key={u.id}
                      type="button"
                      className="nsm-result-item"
                      onClick={() => handleAddUser(u)}
                    >
                      <div className="nsm-avatar">{(u.username || '?')[0].toUpperCase()}</div>
                      <span className="nsm-result-name">{u.username}</span>
                      <span className="nsm-result-add">Add</span>
                    </button>
                  ))}
                </div>
              )}
              {searched && !isSearching && searchResults.length === 0 && (
                <span className="nsm-no-results">No users found</span>
              )}
              {shareError && <span className="nsm-error">{shareError}</span>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NodeShareModal;
