import React from 'react';
import { useParams } from 'react-router-dom';
import { StudyProvider, useStudy } from './studyContext';
import { StudyBoard } from './board/studyBoard';
import { MoveTree } from './sidebar/movetree';

export interface PatchStudyPageProps {
  className?: string;
}

function StudyPageContent({ className }: PatchStudyPageProps) {
  const { id } = useParams<{ id: string }>();
  const { state, clearError } = useStudy();

  return (
    <div className={`patch-study-page ${className || ''}`}>
      {state.error && (
        <div className="patch-study-error-banner" style={{
          backgroundColor: '#ffebee',
          color: '#c62828',
          padding: '10px',
          margin: '10px',
          border: '1px solid #ef9a9a',
          borderRadius: '4px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span><strong>Error:</strong> {state.error.message}</span>
          <button onClick={clearError} style={{
            background: 'none',
            border: 'none',
            color: '#c62828',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}>✕</button>
        </div>
      )}
      <div className="patch-study-header">
        <h2>Patch Study Mode (ID: {id})</h2>
        <p className="patch-study-notice">
          This is the new patch-based study interface. Development in progress.
        </p>
      </div>
      <div className="patch-study-layout">
        <div className="patch-study-sidebar">
          <MoveTree />
        </div>
        <div className="patch-study-main">
          <StudyBoard />
        </div>
      </div>
    </div>
  );
}

export function PatchStudyPage(props: PatchStudyPageProps) {
  return (
    <StudyProvider>
      <StudyPageContent {...props} />
    </StudyProvider>
  );
}

export default PatchStudyPage;
