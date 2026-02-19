import React, { useRef, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { BellIcon } from "@radix-ui/react-icons";
import "./Header.css";
import logoImage from "../../assets/logo.jpg";
import { api } from '@ui/assets/api';

interface HeaderProps {
  username: string | null;
  isAuthed: boolean;
  userRole?: string | null;  // User's role (admin, editor, etc.)
}

interface Notification {
  id: string;
  conversation_id: string;
  sender_name: string | null;
  content: string;
  created_at: string;
}

const CATACHAT_URL = "https://catachat.catachess.com";

const Header: React.FC<HeaderProps> = ({ username, isAuthed, userRole }) => {
  const displayName = username?.trim() || 'Account';
  const rightClickCountRef = useRef(0);
  const rightClickTimerRef = useRef<number | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const [bellOpen, setBellOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const bellRef = useRef<HTMLDivElement>(null);

  // Fetch notifications when user is authed
  useEffect(() => {
    if (!isAuthed) return;
    api.get('/api/catchat/notifications?limit=5')
      .then((data: Notification[]) => setNotifications(data))
      .catch(() => {/* silent — bell just shows empty */});
  }, [isAuthed]);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!bellOpen) return;
    const handler = (e: MouseEvent) => {
      if (bellRef.current && !bellRef.current.contains(e.target as Node)) {
        setBellOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [bellOpen]);

  const handleLogoContextMenu = () => {
    rightClickCountRef.current += 1;
    if (rightClickTimerRef.current) {
      window.clearTimeout(rightClickTimerRef.current);
    }
    rightClickTimerRef.current = window.setTimeout(() => {
      rightClickCountRef.current = 0;
      rightClickTimerRef.current = null;
    }, 1200);

    if (rightClickCountRef.current >= 5) {
      rightClickCountRef.current = 0;
      if (rightClickTimerRef.current) {
        window.clearTimeout(rightClickTimerRef.current);
        rightClickTimerRef.current = null;
      }
      window.open("https://catamaze.catachess.com", "_blank", "noopener,noreferrer");
    }
  };

  const handleLogoClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    // Always navigate to home page
    // No special logic needed - let default Link behavior handle it
  };

  const handleNotificationClick = () => {
    setBellOpen(false);
    const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
    const url = token ? `${CATACHAT_URL}?token=${encodeURIComponent(token)}` : CATACHAT_URL;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <header className="app-header">
      <div className="header-left">
        <Link
          to="/"
          className="logo"
          onClick={handleLogoClick}
          onContextMenu={handleLogoContextMenu}
        >
          <img src={logoImage} alt="ChessorTag" className="logo-image" />
        </Link>
        {/* Navigation links moved here, next to logo */}
        <nav className="header-center">
          <Link to="/workspace-select" className="nav-link">Workspace</Link>
          <Link to="/translate" className="nav-link">Translator</Link>
          <Link to="/blogs" className="nav-link">Blogs</Link>
          <div className="nav-dropdown">
            <span className="nav-link nav-link--dropdown">Analysis</span>
            <div className="nav-dropdown-menu">
              <Link to="/analysis" className="nav-dropdown-item">Analysis Board</Link>
              <Link to="/board-editor" className="nav-dropdown-item">Board Editor</Link>
            </div>
          </div>
          <Link to="/sponsorship" className="nav-link" style={{ color: '#ff8c00', fontWeight: 600 }}>Sponsorship</Link>
        </nav>
      </div>
      <div className="header-right">
        {isAuthed && (
          <div className="bell-wrapper" ref={bellRef}>
            <button
              className="bell-btn"
              aria-label="Messages"
              onClick={() => setBellOpen(o => !o)}
            >
              <BellIcon width={20} height={20} />
              {notifications.length > 0 && (
                <span className="bell-badge">{notifications.length}</span>
              )}
            </button>
            {bellOpen && (
              <div className="bell-dropdown">
                <div className="bell-dropdown-header">Messages</div>
                {notifications.length === 0 ? (
                  <div className="bell-empty">No new messages</div>
                ) : (
                  notifications.map(n => (
                    <button
                      key={n.id}
                      className="bell-item"
                      onClick={handleNotificationClick}
                    >
                      <span className="bell-item-sender">{n.sender_name ?? 'Someone'}</span>
                      <span className="bell-item-content">{n.content}</span>
                    </button>
                  ))
                )}
                <button className="bell-open-chat" onClick={handleNotificationClick}>
                  Open catachat →
                </button>
              </div>
            )}
          </div>
        )}
        {isAuthed ? (
          <Link to="/account" className="username" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {displayName}
            {(userRole === 'admin' || userRole === 'editor') && (
              <span style={{
                display: 'inline-block',
                padding: '2px 8px',
                fontSize: '0.7rem',
                fontWeight: 700,
                color: 'white',
                backgroundColor: userRole === 'admin' ? '#4caf50' : '#2196f3',
                borderRadius: '10px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {userRole}
              </span>
            )}
          </Link>
        ) : (
          <Link to="/login" className="nav-link">Login</Link>
        )}
      </div>
    </header>
  );
};

export default Header;
