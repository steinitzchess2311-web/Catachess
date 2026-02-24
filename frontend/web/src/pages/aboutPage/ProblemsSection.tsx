import React from "react";
import chessbaseImg from "../../assets/chessbase.jpg";
import lichessImg from "../../assets/lichess.png";
import chesstempoImg from "../../assets/chesstempo.jpg";

const ProblemsSection = () => {
  return (
    <div style={{ marginBottom: "60px" }}>
      <h2
        style={{
          fontSize: "2rem",
          fontWeight: 700,
          color: "#0f172a",
          marginBottom: "28px",
          textAlign: "center",
        }}
      >
        The Problem with Existing Tools
      </h2>

      {/* ChessBase - Image Left */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "24px",
          marginBottom: "32px",
          alignItems: "center",
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <div style={{ flex: "0 0 78px" }}>
          <a
            href="https://shop.chessbase.com/en/products/chessbase_17_program_only"
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "block" }}
          >
            <img
              src={chessbaseImg}
              alt="ChessBase"
              style={{
                width: "100%",
                borderRadius: "6px",
                boxShadow: "0 3px 10px rgba(0, 0, 0, 0.12)",
                cursor: "pointer",
                transition: "transform 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.04)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
              }}
            />
          </a>
        </div>
        <div style={{ flex: "1" }}>
          <h3
            style={{
              fontSize: "1.35rem",
              fontWeight: 600,
              color: "#2563eb",
              marginBottom: "12px",
            }}
          >
            ChessBase
          </h3>
          <p
            style={{
              fontSize: "0.98rem",
              lineHeight: "1.7",
              color: "#475569",
            }}
          >
            Pro players are all using ChessBase to keep their chess repertoires and materials
            organized, yet ChessBase is <strong>REALLY unfriendly</strong> towards normal chess
            players: <strong>Extremely unfriendly for Mac users</strong>, and,{" "}
            <strong>EXPENSIVE!</strong>
          </p>
        </div>
      </div>

      {/* Lichess - Image Left */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "24px",
          marginBottom: "32px",
          alignItems: "center",
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <div style={{ flex: "0 0 78px" }}>
          <a
            href="https://lichess.org/study"
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "block" }}
          >
            <img
              src={lichessImg}
              alt="Lichess Study"
              style={{
                width: "100%",
                borderRadius: "6px",
                boxShadow: "0 3px 10px rgba(0, 0, 0, 0.12)",
                cursor: "pointer",
                transition: "transform 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.04)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
              }}
            />
          </a>
        </div>
        <div style={{ flex: "1" }}>
          <h3
            style={{
              fontSize: "1.35rem",
              fontWeight: 600,
              color: "#2563eb",
              marginBottom: "12px",
            }}
          >
            Lichess Study
          </h3>
          <p
            style={{
              fontSize: "0.98rem",
              lineHeight: "1.7",
              color: "#475569",
            }}
          >
            Lichess study is good! However, you <strong>cannot intuitively organize</strong>{" "}
            your materials! You cannot create <strong>folders and subfolders</strong> to keep
            your materials organized.
          </p>
        </div>
      </div>

      {/* ChessTempo - Image Left */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "24px",
          marginBottom: "32px",
          alignItems: "center",
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <div style={{ flex: "0 0 78px" }}>
          <a
            href="https://chesstempo.com/opening-training/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "block" }}
          >
            <img
              src={chesstempoImg}
              alt="ChessTempo"
              style={{
                width: "100%",
                borderRadius: "6px",
                boxShadow: "0 3px 10px rgba(0, 0, 0, 0.12)",
                cursor: "pointer",
                transition: "transform 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.04)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
              }}
            />
          </a>
        </div>
        <div style={{ flex: "1" }}>
          <h3
            style={{
              fontSize: "1.35rem",
              fontWeight: 600,
              color: "#2563eb",
              marginBottom: "12px",
            }}
          >
            ChessTempo Opening
          </h3>
          <p
            style={{
              fontSize: "0.98rem",
              lineHeight: "1.7",
              color: "#475569",
            }}
          >
            ChessTempo opening is also good! But there are{" "}
            <strong>limitations when opening a PGN file</strong>, making it harder to import
            your existing chess materials. Plus, there is <strong>NO DATABASE</strong> for referring.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProblemsSection;
