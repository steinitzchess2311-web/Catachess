import React, { useRef, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { BellIcon, SpeakerLoudIcon } from "@radix-ui/react-icons";
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

interface BroadcastNotif {
  id: string;
  sender_name: string | null;
  content: string;
  created_at: string;
}

const CATACHAT_URL = "https://catachat.catachess.com";
const SEEN_KEY = 'catachat_seen_ids';

function loadSeenIds(): Set<string> {
  try {
    const raw = localStorage.getItem(SEEN_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch { return new Set(); }
}

function saveSeenIds(ids: Set<string>) {
  const arr = [...ids].slice(-200);
  localStorage.setItem(SEEN_KEY, JSON.stringify(arr));
}

const Header: React.FC<HeaderProps> = ({ username, isAuthed, userRole }) => {
  const displayName = username?.trim() || 'Account';
  const rightClickCountRef = useRef(0);
  const rightClickTimerRef = useRef<number | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const [bellOpen, setBellOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [latestBroadcast, setLatestBroadcast] = useState<BroadcastNotif | null>(null);
  const [seenIds, setSeenIds] = useState<Set<string>>(() => loadSeenIds());
  const bellRef = useRef<HTMLDivElement>(null);

  // Fetch notifications + latest broadcast when user is authed
  useEffect(() => {
    if (!isAuthed) return;
    api.get('/api/catchat/notifications?limit=5')
      .then((data: Notification[]) => setNotifications(data))
      .catch(() => {});
    api.get('/api/catchat/broadcasts?limit=1')
      .then((data: BroadcastNotif[]) => setLatestBroadcast(data[0] ?? null))
      .catch(() => {});
  }, [isAuthed]);

  const unseenCount =
    notifications.filter(n => !seenIds.has(n.id)).length +
    (latestBroadcast && !seenIds.has(latestBroadcast.id) ? 1 : 0);

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

  function markSeen(id: string) {
    const next = new Set(seenIds);
    next.add(id);
    setSeenIds(next);
    saveSeenIds(next);
  }

  function openCatachat(path = '') {
    setBellOpen(false);
    const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
    const base = CATACHAT_URL + path;
    const url = token ? `${base}?token=${encodeURIComponent(token)}` : base;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function handleNotificationClick(id: string, senderName: string | null) {
    markSeen(id);
    openCatachat(senderName ? `/chat/${encodeURIComponent(senderName)}` : '');
  }

  function handleBroadcastClick(id: string) {
    markSeen(id);
    openCatachat('/broadcast');
  }

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
          <Link to={isAuthed ? "/workspace/private" : "/workspace/public"} className="nav-link">Workspace</Link>
          <Link to="/play" className="nav-link">Games</Link>
          <Link to="/players" className="nav-link">Players</Link>
          <Link to="/blogs" className="nav-link">Blogs</Link>
          <div className="nav-dropdown">
            <span className="nav-link nav-link--dropdown">Analysis</span>
            <div className="nav-dropdown-menu">
              <Link to="/analysis" className="nav-dropdown-item">Analysis Board</Link>
              <Link to="/board-editor" className="nav-dropdown-item">Board Editor</Link>
            </div>
          </div>
          {/* <Link to="/sponsorship" className="nav-link" style={{ color: '#ff8c00', fontWeight: 600 }}>Sponsorship</Link> */}
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
              {unseenCount > 0 && (
                <span className="bell-badge">{unseenCount}</span>
              )}
            </button>
            {bellOpen && (
              <div className="bell-dropdown">
                <div className="bell-dropdown-header">Messages</div>

                {/* Broadcast — always pinned at top */}
                {latestBroadcast && (
                  <button
                    className={`bell-item bell-item--broadcast ${seenIds.has(latestBroadcast.id) ? 'bell-item--seen' : ''}`}
                    onClick={() => handleBroadcastClick(latestBroadcast.id)}
                  >
                    <span className="bell-item-broadcast-label">
                      <SpeakerLoudIcon width={11} height={11} />
                      Broadcast
                    </span>
                    <span className="bell-item-sender">{latestBroadcast.sender_name ?? 'Admin'}</span>
                    <span className="bell-item-content">{latestBroadcast.content}</span>
                  </button>
                )}

                {/* Regular message notifications */}
                {notifications.length === 0 && !latestBroadcast ? (
                  <div className="bell-empty">No new messages</div>
                ) : (
                  notifications.map(n => (
                    <button
                      key={n.id}
                      className={`bell-item ${seenIds.has(n.id) ? 'bell-item--seen' : ''}`}
                      onClick={() => handleNotificationClick(n.id, n.sender_name)}
                    >
                      <span className="bell-item-sender">{n.sender_name ?? 'Someone'}</span>
                      <span className="bell-item-content">{n.content}</span>
                    </button>
                  ))
                )}

                <button className="bell-open-chat" onClick={() => openCatachat()}>
                  Open catachat →
                </button>
              </div>
            )}
          </div>
        )}
        {isAuthed ? (
          <Link to={`/@${username || ''}`} className="username" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
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
