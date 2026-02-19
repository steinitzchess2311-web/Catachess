import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';

interface UserSearchResult {
  id: string;
  username: string;
}

interface SharedUser {
  user_id: string;
  username: string;
  permission: string;
}

interface ShareModalProps {
  nodeId: string;
  nodeTitle: string;
  onClose: () => void;
}

const PERMISSIONS = [
  { value: 'viewer', label: 'Viewer' },
  { value: 'editor', label: 'Editor' },
  { value: 'commenter', label: 'Commenter' },
];

export function ShareModal({ nodeId, nodeTitle, onClose }: ShareModalProps) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserSearchResult | null>(null);
  const [selectedPermission, setSelectedPermission] = useState('viewer');
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    api.get(`/api/v1/workspace/share/${nodeId}/users`)
      .then((data: SharedUser[]) => setSharedUsers(data))
      .catch(() => {});
  }, [nodeId]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await api.get(`/api/v1/workspace/users/search?q=${encodeURIComponent(query.trim())}`);
        setSearchResults(results as UserSearchResult[]);
        setShowDropdown(true);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  const handleSelectUser = useCallback((user: UserSearchResult) => {
    setSelectedUser(user);
    setQuery(user.username);
    setShowDropdown(false);
    setSearchResults([]);
  }, []);

  const handleAdd = useCallback(async () => {
    if (!selectedUser) return;
    setIsAdding(true);
    setError(null);
    try {
      await api.post(`/api/v1/workspace/share/${nodeId}/users`, {
        user_id: selectedUser.id,
        permission: selectedPermission,
        inherit_to_children: true,
      });
      const updated = await api.get(`/api/v1/workspace/share/${nodeId}/users`);
      setSharedUsers(updated as SharedUser[]);
      setSelectedUser(null);
      setQuery('');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to share');
    } finally {
      setIsAdding(false);
    }
  }, [nodeId, selectedUser, selectedPermission]);

  const handleRevoke = useCallback(async (userId: string) => {
    setError(null);
    try {
      await api.delete(`/api/v1/workspace/share/${nodeId}/users`, { user_id: userId });
      setSharedUsers(prev => prev.filter(u => u.user_id !== userId));
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to revoke');
    }
  }, [nodeId]);

  const handleChangePermission = useCallback(async (userId: string, newPermission: string) => {
    setError(null);
    try {
      await api.put(`/api/v1/workspace/share/${nodeId}/users/role`, {
        user_id: userId,
        new_permission: newPermission,
      });
      setSharedUsers(prev =>
        prev.map(u => u.user_id === userId ? { ...u, permission: newPermission } : u)
      );
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to update permission');
    }
  }, [nodeId]);

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  return (
    <div className="patch-modal-overlay" role="dialog" aria-modal="true" onClick={handleOverlayClick}>
      <div className="patch-modal patch-share-modal">
        <div className="patch-modal-header">
          <h3>Share &ldquo;{nodeTitle}&rdquo;</h3>
          <button type="button" className="patch-modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="patch-share-add-row">
          <div className="patch-share-search-wrap">
            <input
              ref={searchInputRef}
              type="text"
              className="patch-share-search-input"
              placeholder="Search by username..."
              value={query}
              onChange={e => { setQuery(e.target.value); setSelectedUser(null); }}
              onFocus={() => { if (searchResults.length > 0) setShowDropdown(true); }}
              autoComplete="off"
            />
            {isSearching && <span className="patch-share-search-spinner" />}
            {showDropdown && searchResults.length > 0 && (
              <ul className="patch-share-dropdown">
                {searchResults.map(u => (
                  <li key={u.id}>
                    <button
                      type="button"
                      className="patch-share-dropdown-item"
                      onMouseDown={() => handleSelectUser(u)}
                    >
                      {u.username}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {showDropdown && !isSearching && searchResults.length === 0 && query.trim() && (
              <div className="patch-share-dropdown patch-share-dropdown--empty">No users found</div>
            )}
          </div>
          <select
            className="patch-share-permission-select"
            value={selectedPermission}
            onChange={e => setSelectedPermission(e.target.value)}
          >
            {PERMISSIONS.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <button
            type="button"
            className="patch-share-add-btn"
            onClick={handleAdd}
            disabled={!selectedUser || isAdding}
          >
            {isAdding ? 'Adding...' : 'Add'}
          </button>
        </div>

        {error && <div className="patch-share-error">{error}</div>}

        {sharedUsers.length > 0 && (
          <div className="patch-share-list">
            <h4>Shared with</h4>
            <ul>
              {sharedUsers.map(u => (
                <li key={u.user_id} className="patch-share-list-item">
                  <span className="patch-share-list-username">{u.username}</span>
                  <select
                    className="patch-share-permission-select patch-share-permission-select--inline"
                    value={u.permission}
                    onChange={e => handleChangePermission(u.user_id, e.target.value)}
                  >
                    {PERMISSIONS.map(p => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="patch-share-revoke-btn"
                    onClick={() => handleRevoke(u.user_id)}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
