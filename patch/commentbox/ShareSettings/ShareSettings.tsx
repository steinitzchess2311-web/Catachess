import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStudy } from '../../studyContext';
import { api } from '@ui/assets/api';
import { ShareWith } from './ShareWith';

type VisibilityMode = 'public' | 'private' | 'shared';

const VIS = [
  { value: 'public'  as VisibilityMode, icon: '🌐', label: 'Public'     },
  { value: 'private' as VisibilityMode, icon: '🔒', label: 'Private'    },
  { value: 'shared'  as VisibilityMode, icon: '👥', label: 'Share with' },
];

export function ShareSettings() {
  const { state } = useStudy();

  const [visibility, setVisibility] = useState<VisibilityMode>('private');
  const nodeVersionRef               = useRef(1);
  const [visLoading, setVisLoading] = useState(false);
  const [visError, setVisError]     = useState<string | null>(null);

  const isShared = visibility === 'shared';

  // ── Load node visibility ───────────────────────────────────────────────────
  useEffect(() => {
    if (!state.studyId) return;
    api.get(`/api/v1/workspace/nodes/${state.studyId}`)
      .then((n: any) => {
        if (n?.visibility) setVisibility(n.visibility as VisibilityMode);
        if (n?.version)    nodeVersionRef.current = n.version;
      })
      .catch(() => {});
  }, [state.studyId]);

  // ── Change visibility ──────────────────────────────────────────────────────
  const handleVisibilityChange = useCallback(async (next: VisibilityMode) => {
    if (!state.studyId || visLoading) return;
    setVisLoading(true); setVisError(null);
    const prev = visibility; setVisibility(next);
    try {
      await api.put(`/api/v1/workspace/nodes/${state.studyId}`, {
        visibility: next, version: nodeVersionRef.current,
      });
      nodeVersionRef.current += 1;
    } catch {
      setVisibility(prev); setVisError('Failed to update visibility');
    } finally { setVisLoading(false); }
  }, [state.studyId, visibility, visLoading]);

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <span style={sLabel}>Visibility</span>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>

        {/* ── Left: 3 visibility cards (static, never scroll) ──────────── */}
        <div style={{
          display: 'flex', flexDirection: 'column', gap: '4px',
          flexShrink: 0,
          width: isShared ? '50%' : '100%',
          transition: 'width 0.28s cubic-bezier(0.4,0,0.2,1)',
        }}>
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
                <span style={{
                  flex: 1, textAlign: 'left', fontSize: '12px',
                  fontWeight: active ? 600 : 500,
                  color: active ? 'var(--accent, #4e7fff)' : 'inherit',
                }}>
                  {label}
                </span>
                {active && (
                  <span style={{
                    width: '6px', height: '6px', borderRadius: '50%',
                    background: 'var(--accent, #4e7fff)', flexShrink: 0,
                  }} />
                )}
              </button>
            );
          })}

          {visError && (
            <span style={{ fontSize: '10px', color: 'var(--error, #e05252)', marginTop: '2px' }}>
              {visError}
            </span>
          )}
        </div>

        {/* ── Right: ShareWith panel (only mounts when shared) ─────────── */}
        {isShared && state.studyId && (
          <ShareWith studyId={state.studyId} />
        )}
      </div>
    </div>
  );
}

// ── Label style ───────────────────────────────────────────────────────────────
const sLabel: React.CSSProperties = {
  fontSize: '10px', fontWeight: 700, letterSpacing: '0.08em',
  textTransform: 'uppercase', color: 'var(--text-muted, #888)',
};
