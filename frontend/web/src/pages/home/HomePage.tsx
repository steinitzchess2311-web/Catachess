import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@ui/assets/api";
import "./HomePage.css";

interface UserStatistics {
  total_online_seconds: number;
  total_moves_count: number;
  total_online_hours: number;
}

const HomePage: React.FC = () => {
  const [username, setUsername] = useState<string>("");
  const [statistics, setStatistics] = useState<UserStatistics>({
    total_online_seconds: 0,
    total_moves_count: 0,
    total_online_hours: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Fetch user profile for username
        const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
        if (!token) {
          setLoading(false);
          return;
        }

        const [profileResponse, statsResponse] = await Promise.all([
          api.request("/user/profile", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          api.get("/api/v1/user/statistics"),
        ]);

        setUsername(profileResponse.username || "User");
        setStatistics(statsResponse);
      } catch (error) {
        console.error("Failed to fetch user data:", error);
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
        <div className="home-content">
          {/* Left Section - Study Statistics */}
          <div className="left-section">
            <div className="stats-container">
              <h2 className="stats-title">
                Hi {loading ? "..." : username || "User"}
              </h2>

              <div className="stat-item">
                <div className="stat-icon">⏱️</div>
                <div className="stat-content">
                  <p className="stat-text">
                    You've studied chess for{" "}
                    <span className="stat-value">{displayHours}</span> hours
                  </p>
                </div>
              </div>

              <div className="stat-item">
                <div className="stat-icon">♟️</div>
                <div className="stat-content">
                  <p className="stat-text">
                    You've studied{" "}
                    <span className="stat-value">{statistics.total_moves_count}</span> moves
                  </p>
                </div>
              </div>

              <Link to="/workspace-select" className="recent-study-link">
                <span>Go to your recent study</span>
                <span className="arrow">→</span>
              </Link>
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
