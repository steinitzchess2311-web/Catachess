import React, { useEffect, useState } from 'react';
import { getInvite, resetInvite, setInviteActive } from '../api';
import type { InviteInfo } from '../types';

interface Props {
  classroomId: string;
  canManage: boolean;
}

export const InvitePanel: React.FC<Props> = ({ classroomId, canManage }) => {
  const [invite, setInvite] = useState<InviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getInvite(classroomId)
      .then(setInvite)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroomId]);

  async function handleReset() {
    const updated = await resetInvite(classroomId);
    setInvite(updated);
  }

  async function handleToggle() {
    if (!invite) return;
    const updated = await setInviteActive(classroomId, !invite.invite_active);
    setInvite(updated);
  }

  function handleCopy() {
    if (!invite) return;
    navigator.clipboard.writeText(invite.invite_code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  if (loading) return (
    <div className="cl-invite-box">
      <div className="cl-skeleton" style={{ width: 120, height: 32 }} />
    </div>
  );

  if (!invite) return null;

  return (
    <div className="cl-invite-box">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Invite Code
        </span>
        <span className="cl-invite-code" style={{ opacity: invite.invite_active ? 1 : 0.4 }}>
          {invite.invite_code}
        </span>
        {!invite.invite_active && (
          <span style={{ fontSize: '0.76rem', color: 'var(--cl-overdue)', fontWeight: 500 }}>
            Invite link is disabled
          </span>
        )}
      </div>
      <div className="cl-invite-actions">
        <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={handleCopy}>
          {copied ? '✓ Copied' : 'Copy'}
        </button>
        {canManage && (
          <>
            <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={handleReset}>
              Reset
            </button>
            <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={handleToggle}>
              {invite.invite_active ? 'Disable' : 'Enable'}
            </button>
          </>
        )}
      </div>
    </div>
  );
};
