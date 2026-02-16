import React from "react";
import { Link } from "react-router-dom";
import "./HomePage.css";

const HomePage: React.FC = () => {
  // TODO: Replace with actual data from backend
  const studyHours = 0;
  const studiedMoves = 0;

  return (
    <div className="home-page">
      <div className="home-container">
        <div className="home-content">
          {/* Left Section - Study Statistics */}
          <div className="left-section">
            <div className="stats-container">
              <h2 className="stats-title">Your Progress</h2>

              <div className="stat-item">
                <div className="stat-icon">⏱️</div>
                <div className="stat-content">
                  <p className="stat-text">
                    You've studied chess for{" "}
                    <span className="stat-value">{studyHours}</span> hours
                  </p>
                </div>
              </div>

              <div className="stat-item">
                <div className="stat-icon">♟️</div>
                <div className="stat-content">
                  <p className="stat-text">
                    You've studied{" "}
                    <span className="stat-value">{studiedMoves}</span> moves
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
