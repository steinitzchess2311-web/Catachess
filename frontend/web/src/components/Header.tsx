import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

interface HeaderProps {
  username: string | null;
  isAuthed: boolean;
}

const Header: React.FC<HeaderProps> = ({ username, isAuthed }) => {
  const displayName = username?.trim() || 'Account';

  return (
    <header className="app-header">
      <div className="header-left">
        <Link to="/" className="logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="black" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M2 7L12 12L22 7" stroke="black" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M12 22V12" stroke="black" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
          <span className="app-name">Catachess</span>
        </Link>
      </div>
      <nav className="header-center">
        <Link to="/about" className="nav-link">About Us</Link>
      </nav>
      <div className="header-right">
        {isAuthed ? (
          <Link to="/account" className="username">{displayName}</Link>
        ) : (
          <Link to="/login" className="nav-link">Login</Link>
        )}
      </div>
    </header>
  );
};

export default Header;
