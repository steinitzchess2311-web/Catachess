/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Analysis page sidebar engine panel.
*/

import React, { useMemo, useState } from 'react';
import { useStudy } from '@patch/studyContext';
import { useEngineAnalysis } from '@patch/sidebar/hooks/useEngineAnalysis';
import { AnalysisSettings } from '@patch/sidebar/components/AnalysisSettings';
import { AnalysisPanel } from '@patch/sidebar/components/AnalysisPanel';
import { uciLineToSan } from '@patch/chessJS/uci';
import type { EngineMode } from '@patch/engine/types';
import { formatSanWithMoveNumbers } from '@patch/sidebar/utils/formatters';

export function AnalysisSidebar() {
  const { state } = useStudy();
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<EngineMode>('auto');

  const engineAnalysis = useEngineAnalysis({
    enabled: engineEnabled,
    fen: state.currentFen,
    multipv,
    engineMode,
  });

  const formattedLines = useMemo(() => {
    if (!engineAnalysis.analysisFen || engineAnalysis.lines.length === 0) return [];
    const fen = engineAnalysis.analysisFen;
    return engineAnalysis.lines.map((line) => {
      const sanLine = uciLineToSan(line.pv || [], fen);
      const sanMoves = sanLine
        .map((step) => step.san)
        .filter((move): move is string => Boolean(move));
      const sanText = formatSanWithMoveNumbers(sanMoves, fen);
      return { ...line, sanText };
    });
  }, [engineAnalysis.lines, engineAnalysis.analysisFen]);

  return (
    <div className="analysis-sidebar-inner">
      <AnalysisSettings
        currentDepth={engineAnalysis.currentDepth}
        nps={engineAnalysis.nps}
        multipv={multipv}
        onMultipvChange={setMultipv}
        engineMode={engineMode}
        onEngineModeChange={setEngineMode}
        engineEnabled={engineEnabled}
        onEngineEnabledChange={setEngineEnabled}
      />
      <AnalysisPanel
        engineEnabled={engineEnabled}
        lines={formattedLines}
        error={engineAnalysis.error}
        engineLabel={engineMode === 'auto' ? 'Auto engine' : engineMode === 'stockfish' ? 'Stockfish' : 'AlphaZero'}
      />
    </div>
  );
}

export default AnalysisSidebar;
