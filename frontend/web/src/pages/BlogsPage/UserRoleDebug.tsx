/**
 * UserRoleDebug - Debug component to display current user's role
 * Temporarily show in corner to verify permissions
 */

import React from 'react';
import { useUser } from '../../contexts/UserContext';

/**
 * Debug badge showing current user role
 * Remove this component after debugging
 */
const UserRoleDebug: React.FC = () => {
  const { username, userRole, userId } = useUser();

  if (!username) return null;

  const isPrivileged = userRole === 'editor' || userRole === 'admin';

  return (
    <div
      style={{
        position: 'fixed',
        top: '80px',
        right: '20px',
        padding: '12px 16px',
        backgroundColor: isPrivileged ? '#4caf50' : '#ff9800',
        color: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        fontSize: '0.85rem',
        fontWeight: 600,
        zIndex: 9999,
        fontFamily: 'monospace'
      }}
    >
      <div style={{ marginBottom: '4px' }}>
        👤 {username || 'Unknown'}
      </div>
      <div style={{ marginBottom: '4px' }}>
        🎭 Role: {userRole || 'none'}
      </div>
      <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>
        ID: {userId?.substring(0, 8)}...
      </div>
      {!isPrivileged && (
        <div style={{
          marginTop: '8px',
          paddingTop: '8px',
          borderTop: '1px solid rgba(255,255,255,0.3)',
          fontSize: '0.75rem'
        }}>
          ⚠️ Need 'editor' or 'admin' role
        </div>
      )}
    </div>
  );
};

export default UserRoleDebug;
