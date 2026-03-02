import React, { useRef, useState } from 'react';
import { createAssignment, uploadMaterial } from '../api';
import type { Assignment, AssignmentCategory, AssignmentType } from '../types';
import { WorkspacePicker, type PickerNode } from '../../../components/WorkspacePicker';

interface Props {
  classroomId: string;
  onClose: () => void;
  onCreated: (assignment: Assignment) => void;
}

interface WorkspaceSelection {
  id: string;
  title: string;
  node_type: 'folder' | 'study';
}

export const CreateAssignmentModal: React.FC<Props> = ({ classroomId, onClose, onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<AssignmentCategory>('assignment');
  const [type, setType] = useState<AssignmentType>('tactics');
  const [dueDate, setDueDate] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('');
  const [timeLimit, setTimeLimit] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Material-specific state
  const [materialFiles, setMaterialFiles] = useState<File[]>([]);
  const [workspaceSelection, setWorkspaceSelection] = useState<WorkspaceSelection | null>(null);
  const [showWorkspacePicker, setShowWorkspacePicker] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isMaterial = category === 'material';

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Build payload
      const payload: any = {
        title: title.trim(),
        description: description.trim() || undefined,
        category,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        max_attempts: maxAttempts ? parseInt(maxAttempts) : null,
        time_limit: timeLimit ? parseInt(timeLimit) * 60 : null,
        targets: { type: 'all' },
      };

      if (isMaterial) {
        // No type field for material — both workspace + uploads can coexist
        if (!workspaceSelection && materialFiles.length === 0) {
          setError('Please select a workspace item or upload a file.');
          setLoading(false);
          return;
        }
        if (workspaceSelection) {
          payload.source_type = 'study';
          payload.source_ref = JSON.stringify({ study_id: workspaceSelection.id });
        } else {
          payload.source_type = 'upload';
        }
      } else {
        payload.type = type;
      }

      const assignment = await createAssignment(classroomId, payload);

      // Upload all files (sequential to avoid race on source_ref)
      if (isMaterial && materialFiles.length > 0) {
        for (const f of materialFiles) {
          try {
            await uploadMaterial(classroomId, assignment.id, f);
          } catch {
            // Assignment was created but upload failed — still close with success
          }
        }
      }

      onCreated(assignment);
    } catch (err: any) {
      setError(err?.message || 'Failed to create assignment.');
    } finally {
      setLoading(false);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (files) {
      setMaterialFiles(prev => [...prev, ...Array.from(files)]);
    }
    // Reset input so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleWorkspaceSelect(node: PickerNode) {
    setWorkspaceSelection({ id: node.id, title: node.title, node_type: node.node_type });
    setShowWorkspacePicker(false);
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <>
      <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
        <div className="cl-modal cl-modal--wide" role="dialog" aria-modal="true" aria-labelledby="asgn-modal-title">
          <div className="cl-modal__header">
            <h2 className="cl-modal__title" id="asgn-modal-title">New Assignment</h2>
            <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="cl-modal__body">
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-title">Title</label>
                <input
                  id="asgn-title"
                  className="cl-input"
                  placeholder="e.g. Opening Homework #1"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  maxLength={200}
                  autoFocus
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: isMaterial ? '1fr' : '1fr 1fr', gap: '0.75rem' }}>
                <div className="cl-field">
                  <label className="cl-label" htmlFor="asgn-category">Category</label>
                  <select id="asgn-category" className="cl-select" value={category} onChange={e => setCategory(e.target.value as AssignmentCategory)}>
                    <option value="material">Material</option>
                    <option value="assignment">Assignment</option>
                    <option value="exam">Exam</option>
                  </select>
                </div>
                {!isMaterial && (
                  <div className="cl-field">
                    <label className="cl-label" htmlFor="asgn-type">Type</label>
                    <select id="asgn-type" className="cl-select" value={type} onChange={e => setType(e.target.value as AssignmentType)}>
                      <option value="tactics">Tactics</option>
                      <option value="opening">Opening</option>
                      <option value="trainer">Trainer</option>
                      <option value="workspace">Workspace Study</option>
                      <option value="upload">Upload</option>
                    </select>
                  </div>
                )}
              </div>

              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-desc">Description (optional)</label>
                <textarea
                  id="asgn-desc"
                  className="cl-textarea"
                  placeholder="Instructions for students…"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={3}
                />
              </div>

              {/* Material source picker */}
              {isMaterial && (
                <div className="cl-field">
                  <label className="cl-label">Material Source</label>

                  {/* Uploaded files section — only visible when files added */}
                  {materialFiles.length > 0 && (
                    <div style={{ marginBottom: '0.6rem' }}>
                      <p style={{ margin: '0 0 0.4rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                        Uploaded Materials
                      </p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {materialFiles.map((f, i) => (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'center', gap: '0.4rem',
                            background: 'var(--cl-surface, #f8fafc)',
                            border: '1px solid var(--cl-border, #e2e8f0)',
                            borderRadius: 8,
                            padding: '0.45rem 0.6rem',
                          }}>
                            <span style={{ fontSize: '0.9rem' }}>📎</span>
                            <p style={{ margin: 0, flex: 1, fontSize: '0.8rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {f.name}
                            </p>
                            <span style={{ fontSize: '0.72rem', color: 'var(--cl-text-muted)' }}>{formatSize(f.size)}</span>
                            <button
                              type="button"
                              onClick={() => setMaterialFiles(prev => prev.filter((_, idx) => idx !== i))}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', color: 'var(--cl-text-muted)', padding: 0, lineHeight: 1 }}
                            >×</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    style={{ display: 'none' }}
                    onChange={handleFileSelect}
                    accept=".pdf,.pgn,.png,.jpg,.jpeg,.gif,.doc,.docx,.ppt,.pptx,.txt,.zip"
                  />

                  {/* Two side-by-side cards: Upload File | Select from Workspace */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
                    {/* Upload File card */}
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      style={{
                        border: `1.5px solid ${materialFiles.length > 0 ? 'var(--cl-accent, #3b82f6)' : 'var(--cl-border, #e2e8f0)'}`,
                        borderRadius: 10,
                        padding: '0.8rem',
                        cursor: 'pointer',
                        background: materialFiles.length > 0 ? 'var(--cl-accent-light, #eff6ff)' : 'var(--cl-surface, #f8fafc)',
                        transition: 'border-color 0.15s, background 0.15s',
                        minHeight: 72,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                      }}
                    >
                      {materialFiles.length > 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span style={{ fontSize: '1rem' }}>📎</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600 }}>
                              {materialFiles.length} file{materialFiles.length > 1 ? 's' : ''} selected
                            </p>
                            <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--cl-text-muted, #94a3b8)' }}>
                              Click to add more
                            </p>
                          </div>
                        </div>
                      ) : (
                        <>
                          <p style={{ margin: '0 0 2px', fontSize: '0.82rem', fontWeight: 600, color: 'var(--cl-text)' }}>
                            Upload File
                          </p>
                          <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--cl-text-muted, #94a3b8)' }}>
                            PDF, PGN, images, docs…
                          </p>
                        </>
                      )}
                    </div>

                    {/* Workspace card */}
                    <div
                      onClick={() => setShowWorkspacePicker(true)}
                      style={{
                        border: `1.5px solid ${workspaceSelection ? 'var(--cl-accent, #3b82f6)' : 'var(--cl-border, #e2e8f0)'}`,
                        borderRadius: 10,
                        padding: '0.8rem',
                        cursor: 'pointer',
                        background: workspaceSelection ? 'var(--cl-accent-light, #eff6ff)' : 'var(--cl-surface, #f8fafc)',
                        transition: 'border-color 0.15s, background 0.15s',
                        minHeight: 72,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                      }}
                    >
                      {workspaceSelection ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span style={{ fontSize: '1rem' }}>{workspaceSelection.node_type === 'folder' ? '📁' : '📖'}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {workspaceSelection.title}
                            </p>
                            <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--cl-text-muted, #94a3b8)' }}>
                              {workspaceSelection.node_type === 'folder' ? 'Folder' : 'Study'}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={e => { e.stopPropagation(); setWorkspaceSelection(null); }}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.75rem', color: 'var(--cl-accent)', padding: 0, fontWeight: 600 }}
                          >Change</button>
                        </div>
                      ) : (
                        <>
                          <p style={{ margin: '0 0 2px', fontSize: '0.82rem', fontWeight: 600, color: 'var(--cl-text)' }}>
                            Select from Workspace
                          </p>
                          <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--cl-text-muted, #94a3b8)' }}>
                            Study or folder
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: isMaterial ? '1fr' : '1fr 1fr 1fr', gap: '0.75rem' }}>
                <div className="cl-field">
                  <label className="cl-label" htmlFor="asgn-due">Due date (optional)</label>
                  <input
                    id="asgn-due"
                    className="cl-input"
                    type="datetime-local"
                    value={dueDate}
                    min={new Date().toISOString().slice(0, 16)}
                    onChange={e => setDueDate(e.target.value)}
                  />
                </div>
                {!isMaterial && (
                  <>
                    <div className="cl-field">
                      <label className="cl-label" htmlFor="asgn-attempts">Max attempts</label>
                      <input
                        id="asgn-attempts"
                        className="cl-input"
                        type="number"
                        min="1"
                        placeholder="Unlimited"
                        value={maxAttempts}
                        onChange={e => setMaxAttempts(e.target.value)}
                      />
                    </div>
                    <div className="cl-field">
                      <label className="cl-label" htmlFor="asgn-timelimit">Time limit (min)</label>
                      <input
                        id="asgn-timelimit"
                        className="cl-input"
                        type="number"
                        min="1"
                        placeholder="None"
                        value={timeLimit}
                        onChange={e => setTimeLimit(e.target.value)}
                      />
                    </div>
                  </>
                )}
              </div>

              {error && <div className="cl-error-banner">{error}</div>}
            </div>
            <div className="cl-modal__footer">
              <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
              <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !title.trim()}>
                {loading ? 'Publishing…' : 'Publish'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {showWorkspacePicker && (
        <WorkspacePicker
          selectable={['folder', 'study']}
          onSelect={handleWorkspaceSelect}
          onClose={() => setShowWorkspacePicker(false)}
          title="Select Material"
          selectLabel="Select"
        />
      )}
    </>
  );
};
