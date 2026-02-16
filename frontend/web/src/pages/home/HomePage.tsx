import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@ui/assets/api";
import logoImage from "../../assets/logo.jpg";
import "./HomePage.css";

interface UserStatistics {
  total_online_seconds: number;
  total_moves_count: number;
  total_online_hours: number;
}

interface RecentStudy {
  id: string;
  title: string;
  updated_at: string;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>("");
  const [statistics, setStatistics] = useState<UserStatistics>({
    total_online_seconds: 0,
    total_moves_count: 0,
    total_online_hours: 0,
  });
  const [recentStudy, setRecentStudy] = useState<RecentStudy | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
        if (!token) {
          setLoading(false);
          return;
        }

        // Fetch all data in parallel
        const [profileResponse, statsResponse, studiesResponse] = await Promise.all([
          api.get("/api/v1/user/profile"),
          api.get("/api/v1/user/statistics"),
          api.get("/api/v1/workspace/nodes/root/children").catch(() => ({ children: [] })),
        ]);

        setUsername(profileResponse.username || "User");
        setStatistics(statsResponse);

        // Find most recent study
        if (studiesResponse.children && studiesResponse.children.length > 0) {
          const studies = studiesResponse.children
            .filter((node: any) => node.node_type === 'study')
            .sort((a: any, b: any) => {
              const dateA = new Date(a.updated_at || a.created_at).getTime();
              const dateB = new Date(b.updated_at || b.created_at).getTime();
              return dateB - dateA;
            });

          if (studies.length > 0) {
            setRecentStudy({
              id: studies[0].id,
              title: studies[0].title,
              updated_at: studies[0].updated_at || studies[0].created_at,
            });
          }
        }
      } catch (error) {
        console.error("Failed to fetch user data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const displayHours = Math.round(statistics.total_online_hours * 10) / 10;

  const handleRecentStudyClick = () => {
    if (recentStudy) {
      navigate(`/patch/workspace/${recentStudy.id}`);
    } else {
      navigate('/workspace-select');
    }
  };

  return (
    <div className="home-page">
      <div className="home-container">
        {/* Welcome Section */}
        <div className="welcome-section">
          <img src={logoImage} alt="Catachess Logo" className="welcome-logo" />
          <h1 className="welcome-title">Welcome to Catachess!</h1>
          <p className="welcome-subtitle">Your personal chess training platform</p>
        </div>

        <div className="home-content">
          {/* Left Section - Study Statistics */}
          <div className="left-section">
            <div className="stats-container">
              <h2 className="stats-title">
                Hi {loading ? "..." : username || "User"}
              </h2>

              <div className="stats-layout">
                {/* Left side - Statistics */}
                <div className="stats-left">
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

                {/* Right side - Recent Study Button */}
                <div className="stats-right">
                  <button onClick={handleRecentStudyClick} className="recent-study-button">
                    <div className="recent-study-icon">📚</div>
                    <div className="recent-study-content">
                      <span className="recent-study-label">Recent Study</span>
                      {recentStudy ? (
                        <span className="recent-study-title">{recentStudy.title}</span>
                      ) : (
                        <span className="recent-study-title">Go to Workspace</span>
                      )}
                    </div>
                    <span className="arrow">→</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Section - Quick Start */}
          <div className="right-section">
            <div className="quick-start-container">
              <h2 className="stats-title">Quick Start</h2>

              <div className="quick-start-grid">
                {/* Go to Workspace */}
                <Link to="/workspace-select" className="quick-start-card">
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
      </div>
    </div>
  );
};

export default HomePage;
