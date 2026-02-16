import React, { useState, useRef, useEffect } from 'react';
import PageTransition from '../../components/animation/PageTransition';
import './TranslatePage.css';

// 支持的语言列表
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

const TranslatePage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string>('zh-CN'); // 默认简体中文
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 组件卸载时清理轮询
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.pgn')) {
        setError('Please select a PGN file (.pgn)');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  // 清理轮询
  const clearPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  // 轮询查询状态
  const startPolling = (taskId: string) => {
    clearPolling(); // 清除之前的轮询

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`https://translate.catachess.com/translate/status/${taskId}`);

        if (!response.ok) {
          throw new Error('Failed to query translation status');
        }

        const data = await response.json();
        console.log('Translation status:', data.status, 'Progress:', data.progress);

        // 更新状态和进度
        setStatus(data.status);
        setProgress(data.progress || 0);

        // 检查是否完成
        if (data.status === 'completed') {
          clearPolling();
          setLoading(false);

          // 下载翻译后的文件
          if (data.translated_pgn) {
            const blob = new Blob([data.translated_pgn], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file?.name.replace('.pgn', '_translated.pgn') || 'translated.pgn';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            setSuccess(
              `Translation completed! ${data.original_comments_count} comments translated. File downloaded.`
            );

            // 重置表单
            setFile(null);
            setTaskId(null);
            setProgress(0);
            setStatus('');
            if (fileInputRef.current) {
              fileInputRef.current.value = '';
            }
          }
        }

        // 检查是否失败
        if (data.status === 'failed') {
          clearPolling();
          setLoading(false);
          setError(data.error || 'Translation failed. Please try again.');
          setTaskId(null);
          setProgress(0);
          setStatus('');
        }
      } catch (err) {
        clearPolling();
        setLoading(false);
        setError(err instanceof Error ? err.message : 'Failed to query translation status');
        setTaskId(null);
        setProgress(0);
        setStatus('');
      }
    }, 2000); // 每2秒查询一次

    // 超时保护：5分钟后自动停止
    setTimeout(() => {
      if (pollIntervalRef.current) {
        clearPolling();
        setLoading(false);
        setError('Translation timeout. Please try again.');
        setTaskId(null);
        setProgress(0);
        setStatus('');
      }
    }, 300000); // 5分钟
  };

  const handleTranslate = async () => {
    if (!file) {
      setError('Please select a PGN file first');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setProgress(0);
    setStatus('pending');

    try {
      // 读取文件内容
      const pgnContent = await file.text();

      // Step 1: 创建异步翻译任务
      const response = await fetch('https://translate.catachess.com/translate/async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pgn_content: pgnContent,
          target_language: targetLanguage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to create translation task: ${response.status}`);
      }

      const result = await response.json();
      console.log('Task created:', result.task_id);

      // 保存任务ID
      setTaskId(result.task_id);

      // Step 2: 开始轮询查询状态
      startPolling(result.task_id);
    } catch (err) {
      setLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to start translation. Please try again.');
      setProgress(0);
      setStatus('');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();

    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.pgn')) {
        setError('Please select a PGN file (.pgn)');
        return;
      }
      setFile(droppedFile);
      setError(null);
      setSuccess(null);
    }
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
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

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
                      <div className="translate-file-size">
                        {(file.size / 1024).toFixed(2)} KB
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="translate-upload-icon">⬆️</div>
                      <div className="translate-upload-text">
                        Click to upload or drag and drop
                      </div>
                      <div className="translate-upload-hint">PGN files only</div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* 进度显示 */}
            {loading && taskId && (
              <div className="translate-status-box">
                <div className="translate-status-header">
                  <p className="translate-status-text">
                    <strong>Task ID:</strong> {taskId}
                  </p>
                  <p className="translate-status-text">
                    <strong>Status:</strong>{' '}
                    {status === 'pending' && '⏳ Waiting'}
                    {status === 'processing' && '🔄 Translating'}
                    {status === 'completed' && '✅ Completed'}
                    {status === 'failed' && '❌ Failed'}
                  </p>
                  <p className="translate-status-text">
                    <strong>Progress:</strong> {progress}%
                  </p>
                </div>
                <div className="translate-progress-bar">
                  <div
                    className="translate-progress-fill"
                    style={{ width: `${progress}%` }}
                  >
                    {progress}%
                  </div>
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
                <>
                  <span className="translate-spinner"></span>
                  Translating...
                </>
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
