import React, { useEffect, useState } from 'react';
import logoImage from '../../assets/logo.jpg';
import './Loading.css';

interface LoadingProps {
  isLoading: boolean;
  onComplete?: () => void;
}

const Loading: React.FC<LoadingProps> = ({ isLoading, onComplete }) => {
  const [status, setStatus] = useState<'loading' | 'connected' | 'hidden'>('hidden');
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    if (isLoading) {
      setShouldRender(true);
      setStatus('loading');
    } else if (status === 'loading') {
      // Transition to connected
      setStatus('connected');

      // Hide after 1.5 seconds
      const hideTimer = setTimeout(() => {
        setStatus('hidden');
      }, 1500);

      // Remove from DOM after fade out animation
      const removeTimer = setTimeout(() => {
        setShouldRender(false);
        onComplete?.();
      }, 2000);

      return () => {
        clearTimeout(hideTimer);
        clearTimeout(removeTimer);
      };
    }
  }, [isLoading, status, onComplete]);

  if (!shouldRender) return null;

  return (
    <div className={`loading-toast loading-toast--${status}`}>
      <div className="loading-toast__content">
        <img
          src={logoImage}
          alt="Loading"
          className={`loading-toast__logo ${status === 'loading' ? 'loading-toast__logo--spinning' : ''}`}
        />
        <span className="loading-toast__text">
          {status === 'loading' ? 'Loading...' : 'Connected'}
        </span>
      </div>
    </div>
  );
};

export default Loading;
