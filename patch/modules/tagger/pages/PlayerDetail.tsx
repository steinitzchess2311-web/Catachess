import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import UploadPanel from "../components/UploadPanel";
import StatsTable from "../components/StatsTable";
import ConfirmMatchModal from "../components/ConfirmMatchModal";
import { taggerApi, Player, Upload, StatsList, FailedGameItem } from "../api/taggerApi";
import "../styles/tagger.css";

type LogMeta = {
  started?: boolean;
  analysisStarted?: boolean;
  totalLogged?: boolean;
  lastProcessed?: number;
  lastDuplicate?: number;
  statusLogged?: string;
};

const PlayerDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState<Player | null>(null);
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [stats, setStats] = useState<StatsList | null>(null);
  const [failedGames, setFailedGames] = useState<FailedGameItem[]>([]);
  const [activeTab, setActiveTab] = useState<"total" | "white" | "black">("total");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [taggerMode, setTaggerMode] = useState<"cut" | "blackbox">(() => {
    const stored = localStorage.getItem("tagger-mode");
    return stored === "blackbox" ? "blackbox" : "cut";
  });

  const clearTaggerCache = () => {
    const keys = Object.keys(sessionStorage);
    keys.forEach((key) => {
      if (
        key.startsWith("tagger-log-") ||
        key.startsWith("tagger-log-pending-") ||
        key.startsWith("tagger-failed-") ||
        key.startsWith("tagger-meta-") ||
        key.startsWith("tagger-failed-ids-")
      ) {
        sessionStorage.removeItem(key);
      }
    });
  };

  const readCache = <T,>(key: string, fallback: T): T => {
    try {
      const raw = sessionStorage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw) as T;
    } catch {
      return fallback;
    }
  };

  const writeCache = (key: string, value: any) => {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // ignore cache failures
    }
  };

  useEffect(() => {
    clearTaggerCache();
  }, []);

  useEffect(() => {
    localStorage.setItem("tagger-mode", taggerMode);
  }, [taggerMode]);

  const updateLogCache = (upload: Upload) => {
    const logKey = `tagger-log-${upload.id}`;
    const metaKey = `tagger-meta-${upload.id}`;
    const logs = readCache<string[]>(logKey, []);
    const meta = readCache<LogMeta>(metaKey, {});

    if (!meta.started) {
      if (!logs.includes("Upload started.")) {
        logs.push("Upload started.");
      }
      meta.started = true;
    }

    if (!meta.analysisStarted && upload.status === "processing") {
      logs.push("Analysis started.");
      meta.analysisStarted = true;
    }

    if (!meta.totalLogged && upload.total_games && upload.total_games > 0) {
      logs.push(`PGN parsed: total games = ${upload.total_games}.`);
      meta.totalLogged = true;
    }

    if (typeof upload.duplicate_games === "number") {
      const previousDup = meta.lastDuplicate || 0;
      if (upload.duplicate_games > previousDup) {
        const delta = upload.duplicate_games - previousDup;
        logs.push(`Duplicates detected: +${delta} (total ${upload.duplicate_games}).`);
        if (upload.total_games) {
          const remaining = Math.max(upload.total_games - upload.duplicate_games, 0);
          logs.push(`Games to analyze: ${remaining}.`);
        }
        meta.lastDuplicate = upload.duplicate_games;
      }
    }

    const processed = upload.processed_games ?? 0;
    let lastProcessed = meta.lastProcessed || 0;
    if (processed < lastProcessed) {
      logs.length = 0;
      meta.started = false;
      meta.analysisStarted = false;
      meta.totalLogged = false;
      meta.lastDuplicate = 0;
      meta.lastProcessed = 0;
      meta.statusLogged = undefined;
      lastProcessed = 0;
    }
    if (processed > lastProcessed) {
      for (let i = lastProcessed + 1; i <= processed; i += 1) {
        if (i === processed && upload.last_game_index === processed) {
          const status = upload.last_game_status || "processed";
          if (status === "duplicate") {
            logs.push(`Game ${i}: skipped (duplicate).`);
          } else if (status === "processed") {
            const moves = upload.last_game_move_count ?? 0;
            const color = upload.last_game_color || "unknown";
            logs.push(`Game ${i}: analyzed (moves=${moves}, color=${color}).`);
          } else {
            logs.push(`Game ${i}: ${status}.`);
          }
        } else {
          logs.push(`Game ${i}: processed.`);
        }
      }
      meta.lastProcessed = processed;
    }

    if (upload.status && upload.status !== "processing" && meta.statusLogged !== upload.status) {
      logs.push(`Upload status: ${upload.status}.`);
      meta.statusLogged = upload.status;
    }

    writeCache(logKey, logs);
    writeCache(metaKey, meta);
  };

  const fetchAll = async () => {
    if (!id) return;
    setLoading(true);
    setError("");
    try {
      const [playerRes, uploadsRes, statsRes] = await Promise.all([
        taggerApi.getPlayer(id),
        taggerApi.listUploads(id),
        taggerApi.getStats(id),
      ]);
      setPlayer(playerRes);
      setUploads(uploadsRes.uploads || []);
      setStats(statsRes);
      const currentUpload = uploadsRes.uploads?.[0];
      if (currentUpload?.id) {
        const logKey = `tagger-log-${currentUpload.id}`;
        const pendingLogKey = `tagger-log-pending-${id}`;
        const failedKey = `tagger-failed-${currentUpload.id}`;
        const failedIdsKey = `tagger-failed-ids-${currentUpload.id}`;

        const pendingLogs = readCache<string[]>(pendingLogKey, []);
        if (pendingLogs.length) {
          const existingLogs = readCache<string[]>(logKey, []);
          writeCache(logKey, [...pendingLogs, ...existingLogs]);
          sessionStorage.removeItem(pendingLogKey);
        }

        const cachedLogs = readCache<string[]>(logKey, []);
        if (cachedLogs.length || currentUpload.status === "processing") {
          updateLogCache(currentUpload);
        }

        const cachedFailed = readCache<FailedGameItem[]>(failedKey, []);
        const cachedFailedIds = new Set(readCache<number[]>(failedIdsKey, []));
        const shouldFetchFailed =
          cachedFailed.length > 0 || currentUpload.status === "processing";
        if (shouldFetchFailed) {
          try {
            const failed = await taggerApi.getFailedGames(id, currentUpload.id);
            const newFailed: FailedGameItem[] = [];
            failed.failed_games?.forEach((item) => {
              if (!cachedFailedIds.has(item.game_index)) {
                cachedFailedIds.add(item.game_index);
                newFailed.push(item);
              }
            });
            if (newFailed.length) {
              const merged = [...cachedFailed, ...newFailed];
              writeCache(failedKey, merged);
              writeCache(failedIdsKey, Array.from(cachedFailedIds));
              const logKeyValue = readCache<string[]>(logKey, []);
              const updatedLogs = [
                ...logKeyValue,
                ...newFailed.map((item) => `Game ${item.game_index}: failed (${item.error_code}).`),
              ];
              writeCache(logKey, updatedLogs);
            }
            setFailedGames(readCache<FailedGameItem[]>(failedKey, []));
          } catch {
            setFailedGames(readCache<FailedGameItem[]>(failedKey, []));
          }
        } else {
          setFailedGames([]);
        }
      } else {
        setFailedGames([]);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load player.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [id]);

  useEffect(() => {
    if (!uploads[0]?.status) return;
    if (uploads[0].status !== "processing") return;
    const timer = setInterval(() => {
      fetchAll();
    }, 3000);
    return () => clearInterval(timer);
  }, [uploads]);

  const statusLabel = useMemo(() => uploads[0]?.status || "Idle", [uploads]);
  const activeStats = stats?.[activeTab];
  const totalPositions = stats?.total?.stats?.[0]?.total_positions ?? 0;
  const needsConfirmation = uploads[0]?.needs_confirmation ?? false;
  const candidates = uploads[0]?.match_candidates ?? [];
  const logs = uploads[0]?.id
    ? readCache<string[]>(`tagger-log-${uploads[0].id}`, [])
    : id
      ? readCache<string[]>(`tagger-log-pending-${id}`, [])
      : [];

  const handleUpload = async (file: File) => {
    if (!id) return;
    setUploading(true);
    setUploadProgress(0);
    setError("");
    try {
      clearTaggerCache();
      writeCache(`tagger-log-pending-${id}`, [
        "Upload started.",
        `Tagger mode: ${taggerMode}.`,
      ]);
      await taggerApi.uploadPgn(
        id,
        file,
        (value) => setUploadProgress(value),
        taggerMode
      );
      setUploadProgress(100);
      await fetchAll();
    } catch (err: any) {
      setError(err?.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    const confirmed = window.confirm("Delete this player profile? This cannot be undone.");
    if (!confirmed) return;
    setError("");
    try {
      await taggerApi.deletePlayer(id);
      navigate("/playerbase");
    } catch (err: any) {
      setError(err?.message || "Delete failed.");
    }
  };

  const handleRecompute = async () => {
    if (!id) return;
    const confirmed = window.confirm("Recompute all stats? This will overwrite existing results.");
    if (!confirmed) return;
    setError("");
    setRecomputing(true);
    try {
      if (uploads[0]?.id) {
        sessionStorage.removeItem(`tagger-log-${uploads[0].id}`);
        sessionStorage.removeItem(`tagger-meta-${uploads[0].id}`);
        sessionStorage.removeItem(`tagger-failed-${uploads[0].id}`);
        sessionStorage.removeItem(`tagger-failed-ids-${uploads[0].id}`);
      }
      sessionStorage.removeItem(`tagger-log-pending-${id}`);
      await taggerApi.recomputePlayer(id);
      await fetchAll();
    } catch (err: any) {
      setError(err?.message || "Recompute failed.");
    } finally {
      setRecomputing(false);
    }
  };

  const handleExport = async (format: "csv" | "json") => {
    if (!id) return;
    try {
      const blob = await taggerApi.exportStats(id, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${id}_stats.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err?.message || "Export failed.");
    }
  };

  if (loading) {
    return <div className="tagger-page tagger-loading">Loading player...</div>;
  }

  if (!player) {
    return (
      <div className="tagger-page tagger-loading">
        <p>Player not found.</p>
        <button className="tagger-back" onClick={() => navigate("/playerbase")}>
          Back to Players
        </button>
      </div>
    );
  }

  return (
    <section className="tagger-page">
      <div className="tagger-detail-hero">
        <div>
          <button className="tagger-back" onClick={() => navigate("/playerbase")}>
            ← Players
          </button>
          <h1>{player.display_name}</h1>
          <p>Player profile</p>
        </div>
        <div className="tagger-status">
          <span>Status</span>
          <strong>{statusLabel}</strong>
          <small>{totalPositions} positions analyzed</small>
        </div>
      </div>

      <div className="tagger-columns">
        <UploadPanel
          status={statusLabel}
          processedPositions={uploads[0]?.processed_positions ?? 0}
          failedGames={uploads[0]?.failed_games_count ?? 0}
          needsConfirmation={needsConfirmation}
          onUpload={handleUpload}
          uploading={uploading}
          logs={logs}
          uploadProgress={uploadProgress}
          processedGames={uploads[0]?.processed_games ?? 0}
          totalGames={uploads[0]?.total_games ?? 0}
          taggerMode={taggerMode}
          onTaggerModeChange={setTaggerMode}
        />
        <div className="tagger-panel tagger-panel-wide">
          <div className="tagger-panel-header">
            <h2>Tag Breakdown</h2>
            <div className="tagger-tabs">
              {(["total", "white", "black"] as const).map((scope) => (
                <button
                  key={scope}
                  className={activeTab === scope ? "active" : ""}
                  onClick={() => setActiveTab(scope)}
                >
                  {scope}
                </button>
              ))}
            </div>
          </div>

          {activeStats ? (
            <>
              <div className="tagger-meta">
                <div>
                  Engine {activeStats.engine_version} · depth {activeStats.depth}
                  · multipv {activeStats.multipv}
                </div>
                <div>Updated {new Date(activeStats.updated_at).toLocaleString()}</div>
              </div>
              <StatsTable stats={activeStats.stats} />
            </>
          ) : (
            <div className="tagger-empty">No stats yet. Upload a PGN to begin.</div>
          )}

          <div className="tagger-actions">
            <button onClick={() => handleExport("csv")}>Export CSV</button>
            <button onClick={() => handleExport("json")}>Export JSON</button>
            <button className="tagger-recompute" onClick={handleRecompute} disabled={recomputing}>
              {recomputing ? "Recomputing..." : "Recompute Stats"}
            </button>
            <button className="tagger-delete" onClick={handleDelete} disabled={recomputing || uploading}>
              Delete Player
            </button>
          </div>
          {error && <div className="tagger-error">{error}</div>}
        </div>
      </div>

      <div className="tagger-panel tagger-panel-wide">
        <div className="tagger-panel-header">
          <h2>Failed Games</h2>
          <span className="tagger-muted">{failedGames.length} items</span>
        </div>
        {failedGames.length ? (
          <div className="tagger-failed">
            {failedGames.slice(0, 20).map((item) => (
              <div className="tagger-failed-row" key={`${item.game_index}-${item.error_code}`}>
                <span>Game {item.game_index}</span>
                <span className="tagger-failed-code">{item.error_code}</span>
                <span className="tagger-failed-msg">{item.error_message || "—"}</span>
              </div>
            ))}
            {failedGames.length > 20 && (
              <div className="tagger-muted">
                Showing first 20 of {failedGames.length}. Export or retry for full list.
              </div>
            )}
          </div>
        ) : (
          <div className="tagger-empty">No failed games reported.</div>
        )}
      </div>

      <ConfirmMatchModal
        open={needsConfirmation && showModal}
        candidates={candidates}
        onClose={() => setShowModal(false)}
      />
      {needsConfirmation && (
        <button className="tagger-confirm" onClick={() => setShowModal(true)}>
          Review Match Candidates
        </button>
      )}
    </section>
  );
};

export default PlayerDetail;
