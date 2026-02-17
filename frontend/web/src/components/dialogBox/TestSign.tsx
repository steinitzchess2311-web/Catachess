import React, { useState } from 'react';
import './TestSign.css';

interface TestSignProps {
  floating?: boolean;
}

const TestSign: React.FC<TestSignProps> = ({ floating = false }) => {
  return null;
  const [isVisible, setIsVisible] = useState(true);
  // const [showToast, setShowToast] = useState(false);

  // const copyToClipboard = async () => {
  //   const wechatId = 'Cata-Dragon';

  //   try {
  //     await navigator.clipboard.writeText(wechatId);
  //     setShowToast(true);

  //     // Auto-hide toast after 2 seconds
  //     setTimeout(() => {
  //       setShowToast(false);
  //     }, 2000);
  //   } catch (err) {
  //     console.error('Failed to copy:', err);
  //   }
  // };

  if (!isVisible) return null;

  return (
    <>
      <div
        className="test-sign-banner"
        style={floating ? {
          position: 'fixed',
          top: '100px',
          left: 0,
          right: 0,
          zIndex: 999,
        } : undefined}
      >
        <div className="test-sign-content">
          <div className="test-sign-icon">🚧</div>
          <div className="test-sign-text">
            <strong>Currently under renovation.</strong> Beta testers are welcomed to send your suggestions to{' '}
            <a href="mailto:info@steinitzchess.org" className="test-sign-link">
              info@steinitzchess.org
            </a>
            {/* {' '}
            or WeChat{' '}
            <span className="test-sign-wechat" onClick={copyToClipboard}>
              Cata-Dragon
            </span> */}
          </div>
        </div>
        <button
          className="test-sign-close"
          onClick={() => setIsVisible(false)}
          aria-label="Close notification"
        >
          ×
        </button>
      </div>

      {/* {showToast && (
        <div className="test-sign-toast">
          <span className="test-sign-toast-icon">✓</span>
          <span>Copied to clipboard</span>
        </div>
      )} */}
    </>
  );
};

export default TestSign;
