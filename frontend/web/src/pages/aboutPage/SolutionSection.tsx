import React from "react";
import logo from "../../assets/chessortag_pure_logo.png";

const SolutionSection = () => {
  return (
    <div
      style={{
        background: "transparent",
        padding: "24px",
        marginBottom: "60px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "20px",
          marginBottom: "28px",
        }}
      >
        <img
          src={logo}
          alt="ChessorTag Logo"
          style={{
            width: "80px",
            height: "80px",
            objectFit: "contain",
          }}
        />
        <h2
          style={{
            fontSize: "2.1rem",
            fontWeight: 700,
            color: "#2563eb",
            margin: 0,
          }}
        >
          ChessorTag: the Solution.
        </h2>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "20px",
          maxWidth: "960px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            background: "#ffffff",
            border: "1px solid var(--border)",
            padding: "20px",
            borderRadius: "12px",
            boxShadow: "var(--shadow-1)",
          }}
        >
          <h3
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "#2563eb",
              marginBottom: "10px",
            }}
          >
            FREE!
          </h3>
          <p style={{ fontSize: "0.98rem", color: "#475569", lineHeight: "1.6" }}>
            FREE for all users! No premium tiers, no hidden costs. Ads only shows on footer and blogs. Never affect users' experience!
          </p>
        </div>
        <div
          style={{
            background: "#ffffff",
            border: "1px solid var(--border)",
            padding: "20px",
            borderRadius: "12px",
            boxShadow: "var(--shadow-1)",
          }}
        >
          <h3
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "#2563eb",
              marginBottom: "10px",
            }}
          >
            Organized
          </h3>
          <p style={{ fontSize: "0.98rem", color: "#475569", lineHeight: "1.6" }}>
            Easily create folder and subfolder systems to keep everything neat.
          </p>
        </div>
        <div
          style={{
            background: "#ffffff",
            border: "1px solid var(--border)",
            padding: "20px",
            borderRadius: "12px",
            boxShadow: "var(--shadow-1)",
          }}
        >
          <h3
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "#2563eb",
              marginBottom: "10px",
            }}
          >
            Clear PGN
          </h3>
          <p style={{ fontSize: "0.98rem", color: "#475569", lineHeight: "1.6" }}>
            CLEAR PGN parsing technology - import large PGN files seamlessly.
          </p>
        </div>
        <div
          style={{
            background: "#ffffff",
            border: "1px solid var(--border)",
            padding: "20px",
            borderRadius: "12px",
            boxShadow: "var(--shadow-1)",
          }}
        >
          <h3
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "#2563eb",
              marginBottom: "10px",
            }}
          >
            Comprehensive Database
          </h3>
          <p style={{ fontSize: "0.98rem", color: "#475569", lineHeight: "1.6" }}>
            Tired of deploying databases? We've got you covered! Complete{" "}
            <a
              href="https://theweekinchess.com/"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "#2563eb",
                textDecoration: "underline",
                fontWeight: 600,
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#1d4ed8";
                e.currentTarget.style.textDecorationThickness = "2px";
                e.currentTarget.style.transform = "scale(1.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "#2563eb";
                e.currentTarget.style.textDecorationThickness = "1px";
                e.currentTarget.style.transform = "scale(1)";
              }}
            >
              TWIC
            </a>{" "}
            database is fully integrated and ready to use online!
          </p>
        </div>
      </div>
    </div>
  );
};

export default SolutionSection;
