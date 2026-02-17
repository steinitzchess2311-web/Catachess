import React, { useMemo, useState } from 'react';
import { useStudy } from '@patch/studyContext';
import { useEngineAnalysis } from '@patch/sidebar/hooks/useEngineAnalysis';
import { AnalysisSettings } from '@patch/sidebar/components/AnalysisSettings';
import { AnalysisPanel } from '@patch/sidebar/components/AnalysisPanel';
import { uciLineToSan } from '@patch/chessJS/uci';
import { formatSanWithMoveNumbers } from '@patch/sidebar/utils/formatters';

export function AnalysisSidebar() {
  const { state } = useStudy();
  const [depth, setDepth] = useState(14);
  const [multipv, setMultipv] = useState(3);
  const [engineEnabled, setEngineEnabled] = useState(false);

  const engineAnalysis = useEngineAnalysis({
    enabled: engineEnabled,
    fen: state.currentFen,
    depth,
    multipv,
  });

  const formattedLines = useMemo(() => {
    if (engineAnalysis.lines.length === 0) return [];
    return engineAnalysis.lines.map((line) => {
      const sanLine = uciLineToSan(line.pv || [], state.currentFen);
      const sanMoves = sanLine
        .map((step) => step.san)
        .filter((move): move is string => Boolean(move));
      const sanText = formatSanWithMoveNumbers(sanMoves, state.currentFen);
      return { ...line, sanText };
    });
  }, [engineAnalysis.lines, state.currentFen]);

  return (
    <div className="analysis-sidebar-inner">
      <AnalysisSettings
        depth={depth}
        onDepthChange={setDepth}
        multipv={multipv}
        onMultipvChange={setMultipv}
        engineEnabled={engineEnabled}
        onEngineEnabledChange={setEngineEnabled}
      />
      <AnalysisPanel
        engineEnabled={engineEnabled}
        lines={formattedLines}
        status={engineAnalysis.status}
        health={engineAnalysis.health}
        error={engineAnalysis.error}
        lastUpdated={engineAnalysis.lastUpdated}
        engineOrigin={engineAnalysis.engineOrigin}
      />
    </div>
  );
}

export default AnalysisSidebar;
