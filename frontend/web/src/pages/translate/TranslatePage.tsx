import React, { useState, useRef } from 'react';
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
  const [targetLanguage, setTargetLanguage] = useState<string>('zh-CN');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleTranslate = async () => {
    if (!file) {
      setError('Please select a PGN file first');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', targetLanguage);

    try {
      // POST /translate/file — 文件上传，直接返回翻译后的文件
      const response = await fetch('https://translate.catachess.com/translate/file', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Translation failed with status ${response.status}`);
      }

      // 从响应头获取文件名
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = file.name.replace('.pgn', '_translated.pgn');
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      // 下载文件
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // 从响应头读取统计信息
      const originalCount = response.headers.get('X-Original-Comments');
      const translatedCount = response.headers.get('X-Translated-Comments');
      const countInfo = originalCount ? ` ${translatedCount}/${originalCount} comments translated.` : '';

      setSuccess(`Translation completed!${countInfo} File downloaded.`);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed. Please try again.');
    } finally {
      setLoading(false);
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
