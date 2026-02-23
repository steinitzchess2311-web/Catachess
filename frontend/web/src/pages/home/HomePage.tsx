import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@ui/assets/api";
import logoImage from "../../assets/logo.jpg";
import "./HomePage.css";
import { useUser } from "../../contexts/UserContext";

interface UserStatistics {
  total_online_seconds: number;
  total_moves_count: number;
  total_online_hours: number;
}


const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { username } = useUser();
  const [statistics, setStatistics] = useState<UserStatistics>({
    total_online_seconds: 0,
    total_moves_count: 0,
    total_online_hours: 0,
  });
  const [loading, setLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
        if (!token) {
          setIsAuthed(false);
          setLoading(false);
          return;
        }

        const statsResponse = await api.get("/user/statistics");
        setStatistics(statsResponse);
        setIsAuthed(true);
      } catch (error) {
        console.error("Failed to fetch user data:", error);
        setIsAuthed(false);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const displayHours = Math.round(statistics.total_online_hours * 10) / 10;

  return (
    <div className="home-page">
      <div className="home-container">
        {/* Welcome Section */}
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

        <div className="home-content">
          {false && (
          <div className="left-section">
            {loading ? (
              <div className="stats-container">
                <h2 className="stats-title">Loading...</h2>
              </div>
            ) : isAuthed ? (
              <div className="stats-container">
                <h2 className="stats-title">
                  Track your progress!
                </h2>

                <div className="stats-layout">
                  <div className="stat-item-compact">
                    <div className="stat-icon-compact">⏱️</div>
                    <div className="stat-content-compact">
                      <p className="stat-label">Study Time</p>
                      <p className="stat-value-large">{displayHours}h</p>
                    </div>
                  </div>

                  <div className="stat-item-compact">
                    <div className="stat-icon-compact">♟️</div>
                    <div className="stat-content-compact">
                      <p className="stat-label">Moves</p>
                      <p className="stat-value-large">{statistics.total_moves_count}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="stats-container stats-container-login" onClick={() => navigate('/login')}>
                <h2 className="stats-title">
                  Start via login!
                </h2>
                <div className="login-message">
                  <p className="login-text">Your best option for chess studying!</p>
                </div>
              </div>
            )}
          </div>

          )}
          {/* Quick Start Cards */}
          <div className="quick-start-grid">
            {/* Go to Workspace */}
            <Link to="/workspace/private" className="quick-start-card">
              <div className="card-icon">📁</div>
              <h3 className="card-title">Go to Workspace</h3>
              <p className="card-description">
                Access your chess studies and analysis workspace
              </p>
            </Link>

            {/* Translate Material */}
            <Link to="/translate" className="quick-start-card">
              <div className="card-icon">🌐</div>
              <h3 className="card-title">Translate Material</h3>
              <p className="card-description">
                Translate chess notation and terminology
              </p>
            </Link>

            {/* View Blogs */}
            <Link to="/blogs" className="quick-start-card">
              <div className="card-icon">📝</div>
              <h3 className="card-title">View Blogs</h3>
              <p className="card-description">
                Read chess articles and analysis
              </p>
            </Link>

            {/* Prepare Against Opponent - Placeholder */}
            <div className="quick-start-card quick-start-card-disabled">
              <div className="card-icon">🎯</div>
              <h3 className="card-title">Prepare Against Opponent</h3>
              <p className="card-description">
                Coming soon: Analyze opponent games and prepare openings
              </p>
              <span className="card-badge">Coming Soon</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
