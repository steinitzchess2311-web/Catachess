import React, { useRef } from "react";
import { Link, useLocation, useNavigate } from 'react-router-dom';
import "./Header.css";
import logoImage from "../../assets/logo.jpg";

interface HeaderProps {
  username: string | null;
  isAuthed: boolean;
  userRole?: string | null;  // User's role (admin, editor, etc.)
}

const Header: React.FC<HeaderProps> = ({ username, isAuthed, userRole }) => {
  const displayName = username?.trim() || 'Account';
  const rightClickCountRef = useRef(0);
  const rightClickTimerRef = useRef<number | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

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
          <Link to="/sponsorship" className="nav-link" style={{ color: '#ff8c00', fontWeight: 600 }}>Sponsorship</Link>
        </nav>
      </div>
      <div className="header-right">
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
