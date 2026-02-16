import React from "react";
import { Link } from "react-router-dom";
import "./HomePage.css";

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      <div className="home-container">
        <h1 className="home-title">Quick Start</h1>

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
  );
};

export default HomePage;
