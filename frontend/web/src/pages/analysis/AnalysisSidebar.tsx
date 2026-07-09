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
import { ImitatorSettings } from '@patch/sidebar/components/ImitatorSettings';
import { ImitatorPanel } from '@patch/sidebar/components/ImitatorPanel';
import { usePredictor, type PredictorProvider } from '@patch/sidebar/hooks/useImitator';
import { uciLineToSan } from '@patch/chessJS/uci';
import type { EngineMode } from '@patch/engine/types';
import { formatSanWithMoveNumbers } from '@patch/sidebar/utils/formatters';

export function AnalysisSidebar() {
  const { state } = useStudy();
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);
  const [engineMode, setEngineMode] = useState<EngineMode>('auto');
  const [activeTab, setActiveTab] = useState<'analysis' | 'predictor'>('analysis');
  const [predictorProvider, setPredictorProvider] = useState<PredictorProvider>('maia');
  const [predictorTopK, setPredictorTopK] = useState(5);
  const [predictorElo, setPredictorElo] = useState(1500);
  const [predictorEnabled, setPredictorEnabled] = useState(false);

  const engineAnalysis = useEngineAnalysis({
    enabled: activeTab === 'analysis' && engineEnabled,
    fen: state.currentFen,
    multipv,
    engineMode,
  });

  const predictor = usePredictor({
    enabled: activeTab === 'predictor' && predictorEnabled,
    fen: state.currentFen,
    provider: predictorProvider,
    topK: predictorTopK,
    elo: predictorElo,
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
      <div className="patch-sidebar-tabs">
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'analysis' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          Analysis
        </button>
        <button
          type="button"
          className={`patch-sidebar-tab${activeTab === 'predictor' ? ' is-active' : ''}`}
          onClick={() => setActiveTab('predictor')}
        >
          Predictor
        </button>
      </div>
      {activeTab === 'analysis' && (
        <>
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
            engineLabel={engineMode === 'auto' ? 'Auto engine' : engineMode === 'stockfish' ? 'Stockfish' : engineMode === 'lc0' ? 'Leela/LC0' : 'AlphaZero'}
          />
        </>
      )}
      {activeTab === 'predictor' && (
        <>
          <ImitatorSettings
            provider={predictorProvider}
            onProviderChange={setPredictorProvider}
            topK={predictorTopK}
            onTopKChange={setPredictorTopK}
            elo={predictorElo}
            onEloChange={setPredictorElo}
            enabled={predictorEnabled}
            onEnabledChange={setPredictorEnabled}
          />
          <ImitatorPanel result={predictor.result} />
        </>
      )}
    </div>
  );
}

export default AnalysisSidebar;
