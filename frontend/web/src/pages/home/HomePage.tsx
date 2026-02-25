import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@ui/assets/api";
import logoImage from "../../assets/logo.jpg";
import "./HomePage.css";
import { useUser } from "../../contexts/UserContext";
import {
  LayersIcon,
  TargetIcon,
  ReaderIcon,
  ChatBubbleIcon,
  MagnifyingGlassIcon,
  BarChartIcon,
  DesktopIcon,
  PersonIcon,
} from "@radix-ui/react-icons";

interface UserStatistics {
  total_online_seconds: number;
  total_moves_count: number;
  total_online_hours: number;
}

interface HpCardProps {
  to?: string;
  href?: string;
  icon: React.ReactNode;
  label: string;
  tooltip: string;
  disabled?: boolean;
}

const HpCard: React.FC<HpCardProps> = ({ to, href, icon, label, tooltip, disabled }) => {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const inner = (
    <div
      ref={ref}
      className={`hp-card${disabled ? " hp-card--disabled" : ""}`}
      onMouseEnter={() => !disabled && setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <div className="hp-card-icon">{icon}</div>
      <span className="hp-card-label">{label}</span>
      {disabled && <span className="hp-coming-badge">Soon</span>}
      {show && !disabled && (
        <div className="hp-tooltip">{tooltip}</div>
      )}
    </div>
  );

  if (disabled) return inner;
  if (href) return <a href={href} target="_blank" rel="noopener noreferrer" className="hp-card-link">{inner}</a>;
  if (to) return <Link to={to} className="hp-card-link">{inner}</Link>;
  return inner;
};

const HomePage: React.FC = () => {
  const { username } = useUser();
  const [loading, setLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
        if (!token) { setIsAuthed(false); setLoading(false); return; }
        await api.get("/user/statistics");
        setIsAuthed(true);
      } catch {
        setIsAuthed(false);
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, []);

  return (
    <div className="home-page">
      <div className="home-container">

        {/* Welcome */}
        <div className="welcome-section">
          <div className="welcome-brand">
            <img src={logoImage} alt="Catachess Logo" className="welcome-logo" />
            <h1 className="welcome-title">Welcome to Catachess!</h1>
          </div>
          <div className="welcome-taglines">
            <Link to="/about" className="tagline-amateurs">Best platform for amateurs</Link>
            <Link to="/about" className="tagline-coaches">Best choice for Coaches</Link>
          </div>
        </div>

        {/* Grid */}
        <div className="hp-grid">

          {/* Row 1: Study Chess + Community */}
          <div className="hp-row">
            <div className="hp-section">
              <p className="hp-section-label">Study Chess</p>
              <div className="hp-cards">
                <HpCard
                  to="/workspace/private"
                  icon={<LayersIcon width={28} height={28} />}
                  label="WORKSPACE"
                  tooltip="Your online chessbase — share, organize your chess study"
                />
                <HpCard
                  to="/play"
                  icon={<TargetIcon width={28} height={28} />}
                  label="GAMES"
                  tooltip="Not just chess games — have to be out of your expectation!"
                />
              </div>
            </div>

            <div className="hp-section">
              <p className="hp-section-label">Community</p>
              <div className="hp-cards">
                <HpCard
                  to="/blogs"
                  icon={<ReaderIcon width={28} height={28} />}
                  label="BLOGS"
                  tooltip="Read and share chess articles, analysis, and ideas"
                />
                <HpCard
                  href="https://catachat.catachess.com"
                  icon={<ChatBubbleIcon width={28} height={28} />}
                  label="CATACHAT"
                  tooltip="Chat with the chess community in real time"
                />
              </div>
            </div>
          </div>

          {/* Row 2: HUGE Database + Coach Tools */}
          <div className="hp-row">
            <div className="hp-section">
              <p className="hp-section-label">HUGE Database</p>
              <div className="hp-cards">
                <HpCard
                  to="/playerbase"
                  icon={<MagnifyingGlassIcon width={28} height={28} />}
                  label="SEARCH PLAYERS"
                  tooltip="Explore any player's game history and statistics"
                />
                <HpCard
                  to="/analysis?tab=explorer"
                  icon={<BarChartIcon width={28} height={28} />}
                  label="ANALYSIS"
                  tooltip="Dive into millions of games with the opening explorer"
                />
              </div>
            </div>

            <div className="hp-section">
              <p className="hp-section-label">Coach Tools</p>
              <div className="hp-cards">
                <HpCard
                  icon={<DesktopIcon width={28} height={28} />}
                  label="CLASSROOM"
                  tooltip=""
                  disabled
                />
                <HpCard
                  icon={<PersonIcon width={28} height={28} />}
                  label="STUDENTS"
                  tooltip=""
                  disabled
                />
              </div>
            </div>
          </div>

          {/* Powerful Utils — commented out */}
          {/*
          <div className="hp-section">
            <p className="hp-section-label">Powerful Utils</p>
            <div className="hp-cards">
              <HpCard
                to="/translate"
                icon={<GlobeIcon width={28} height={28} />}
                label="TRANSLATE"
                tooltip="Translate chess notation and study material instantly"
              />
            </div>
          </div>
          */}

        </div>
      </div>
    </div>
  );
};

export default HomePage;
