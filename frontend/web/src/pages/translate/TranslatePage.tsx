import React, { useState, useRef, useEffect } from 'react';
import PageTransition from '../../components/animation/PageTransition';
import './TranslatePage.css';

const LANGUAGES = [
  { code: 'zh-CN', name: '简体中文' },
  { code: 'zh-TW', name: '繁体中文' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'es', name: 'Español' },
  { code: 'ru', name: 'Русский' },
  { code: 'it', name: 'Italiano' },
  { code: 'pt', name: 'Português' }
];

const API_BASE = 'https://translate.catachess.com';

const TranslatePage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string>('zh-CN');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [taskStatus, setTaskStatus] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const downloadPgn = (content: string, originalName: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = originalName.replace('.pgn', '_translated.pgn');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    if (!selected.name.endsWith('.pgn')) {
      setError('Please select a PGN file (.pgn)');
      setFile(null);
      return;
    }
    setFile(selected);
    setError(null);
    setSuccess(null);
  };

  const handleTranslate = async () => {
    if (!file) { setError('Please select a PGN file first'); return; }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setProgress(0);
    setTaskStatus('pending');

    try {
      // Step 1: 读取文件内容，POST /translate/async
      const pgnContent = await file.text();
      const res = await fetch(`${API_BASE}/translate/async`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pgn_content: pgnContent, target_language: targetLanguage }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Failed to create task (${res.status})`);
      }

      const { task_id } = await res.json();

      // Step 2: 轮询 GET /translate/status/{task_id}，每2秒
      const fileName = file.name;
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/translate/status/${task_id}`);
          if (!statusRes.ok) throw new Error('Failed to query status');

          const data = await statusRes.json();
          setProgress(data.progress ?? 0);
          setTaskStatus(data.status);

          if (data.status === 'completed') {
            stopPolling();
            setLoading(false);
            // Step 3: 拿 translated_pgn 组装成文件下载
            downloadPgn(data.translated_pgn, fileName);
            setSuccess(
              `Translation completed! ${data.original_comments_count} comments translated. File downloaded.`
            );
            setFile(null);
            setProgress(0);
            setTaskStatus('');
            if (fileInputRef.current) fileInputRef.current.value = '';
          }

          if (data.status === 'failed') {
            stopPolling();
            setLoading(false);
            setError(data.error || 'Translation failed. Please try again.');
            setProgress(0);
            setTaskStatus('');
          }
        } catch (err) {
          stopPolling();
          setLoading(false);
          setError(err instanceof Error ? err.message : 'Failed to query status');
          setProgress(0);
          setTaskStatus('');
        }
      }, 2000);

    } catch (err) {
      setLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to start translation.');
      setProgress(0);
      setTaskStatus('');
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); e.stopPropagation();
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;
    if (!dropped.name.endsWith('.pgn')) {
      setError('Please select a PGN file (.pgn)');
      return;
    }
    setFile(dropped);
    setError(null);
    setSuccess(null);
  };

  const statusLabel: Record<string, string> = {
    pending: '⏳ Waiting',
    processing: '🔄 Translating',
    completed: '✅ Completed',
    failed: '❌ Failed',
  };

  return (
    <PageTransition>
      <div className="translate-page">
        <div className="translate-container">
          <div className="translate-header">
            <h1 className="translate-title">PGN Translator</h1>
            <p className="translate-subtitle">
              Translate chess game annotations to your preferred language
            </p>
          </div>

          <div className="translate-card">
            {/* 语言选择 */}
            <div className="translate-section">
              <label className="translate-label">Target Language</label>
              <select
                className="translate-language-select"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                disabled={loading}
              >
                {LANGUAGES.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            {/* 文件上传 */}
            <div className="translate-section">
              <label className="translate-label">Upload PGN File</label>
              <div
                className={`translate-dropzone ${file ? 'has-file' : ''}`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pgn"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  disabled={loading}
                />
                <div className="translate-dropzone-content">
                  {file ? (
                    <>
                      <div className="translate-file-icon">📄</div>
                      <div className="translate-file-name">{file.name}</div>
                      <div className="translate-file-size">{(file.size / 1024).toFixed(2)} KB</div>
                    </>
                  ) : (
                    <>
                      <div className="translate-upload-icon">⬆️</div>
                      <div className="translate-upload-text">Click to upload or drag and drop</div>
                      <div className="translate-upload-hint">PGN files only</div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* 进度条 */}
            {loading && (
              <div className="translate-status-box">
                <div className="translate-status-row">
                  <span className="translate-status-label">
                    {statusLabel[taskStatus] || '⏳ Waiting'}
                  </span>
                  <span className="translate-status-percent">{progress}%</span>
                </div>
                <div className="translate-progress-bar">
                  <div className="translate-progress-fill" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}

            {error && (
              <div className="translate-message translate-error">
                <span className="translate-message-icon">⚠️</span>
                {error}
              </div>
            )}

            {success && (
              <div className="translate-message translate-success">
                <span className="translate-message-icon">✅</span>
                {success}
              </div>
            )}

            <button
              className="translate-button"
              onClick={handleTranslate}
              disabled={loading || !file}
            >
              {loading ? (
                <><span className="translate-spinner"></span>Translating...</>
              ) : (
                'Translate'
              )}
            </button>

            <div className="translate-info">
              <h3 className="translate-info-title">How it works</h3>
              <ol className="translate-info-list">
                <li>Select your target language from the dropdown</li>
                <li>Upload a PGN file containing chess games with annotations</li>
                <li>Click "Translate" to convert all annotations to your chosen language</li>
                <li>The translated file will be automatically downloaded</li>
                <li>Your PGN file must include proper game headers (Event, Site, Date, etc.)</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
};

export default TranslatePage;
