import React from "react";

const ImitatorSection = () => {
  return (
    <div style={{ background: "transparent", marginBottom: "60px" }}>
      {/* Title */}
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h2
          style={{
            fontSize: "2rem",
            fontWeight: 800,
            color: "#0f172a",
            marginBottom: "12px",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
        >
          Now, Our central Innovation...
        </h2>
        <h3
          style={{
            fontSize: "1.7rem",
            fontWeight: 700,
            color: "#2563eb",
            marginBottom: "0",
          }}
        >
          ChessorTag Imitator!
        </h3>
      </div>

      {/* Card 1: How it works? */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <h4
          style={{
            fontSize: "1.35rem",
            fontWeight: 600,
            color: "#2563eb",
            marginBottom: "12px",
          }}
        >
          How it works?
        </h4>
        <p
          style={{
            fontSize: "0.98rem",
            lineHeight: "1.7",
            color: "#475569",
            margin: "0",
          }}
        >
          We developed our tagger algorithm, which gives each chess move one or more tags, and
          calculates the percentage of different tags in all player's games. We do the imitation
          by calculating the similarities between Stockfish moves and player's tag percentage.
        </p>
      </div>

      {/* Card 2: What does it do? */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <h4
          style={{
            fontSize: "1.35rem",
            fontWeight: 600,
            color: "#2563eb",
            marginBottom: "12px",
          }}
        >
          What does it do?
        </h4>
        <ul
          style={{
            fontSize: "0.98rem",
            lineHeight: "1.7",
            color: "#475569",
            paddingLeft: "0",
            listStyleType: "none",
            margin: "0",
          }}
        >
          <li style={{ marginBottom: "12px", paddingLeft: "24px", position: "relative" }}>
            <span
              style={{
                position: "absolute",
                left: "0",
                color: "#2563eb",
                fontWeight: 700,
              }}
            >
              ✓
            </span>
            Helps you to <strong>prepare against your opponent easily!</strong> You can have
            clear focus on which opening variation to study deeper when preparing!
          </li>
          <li style={{ marginBottom: "0", paddingLeft: "24px", position: "relative" }}>
            <span
              style={{
                position: "absolute",
                left: "0",
                color: "#2563eb",
                fontWeight: 700,
              }}
            >
              ✓
            </span>
            Allows LLMs to <strong>explain moves in the style of a target player</strong> (which
            is epoch-making).
          </li>
        </ul>
      </div>

      {/* Card 3: Why is it important? */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "var(--shadow-1)",
          width: "min(100%, 960px)",
          margin: "0 auto 32px auto",
        }}
      >
        <h4
          style={{
            fontSize: "1.35rem",
            fontWeight: 600,
            color: "#2563eb",
            marginBottom: "12px",
          }}
        >
          Why is it important?
        </h4>
        <ul
          style={{
            fontSize: "0.98rem",
            lineHeight: "1.7",
            color: "#475569",
            paddingLeft: "0",
            listStyleType: "none",
            margin: "0",
          }}
        >
          <li style={{ marginBottom: "12px", paddingLeft: "24px", position: "relative" }}>
            <span
              style={{
                position: "absolute",
                left: "0",
                color: "#2563eb",
                fontWeight: 700,
              }}
            >
              •
            </span>
            This is the <strong>BEST AI-powered chess coaching system</strong>! Unlike human
            coaches, it's available 24/7 and learns from the world's greatest players.
          </li>
          <li style={{ marginBottom: "12px", paddingLeft: "24px", position: "relative" }}>
            <span
              style={{
                position: "absolute",
                left: "0",
                color: "#2563eb",
                fontWeight: 700,
              }}
            >
              •
            </span>
            If you give an FEN to ChatGPT or Gemini, they generate wrong ideas. But with our
            system, <strong>LLMs can actively reflect what players are thinking</strong>.
          </li>
          <li style={{ marginBottom: "0", paddingLeft: "24px", position: "relative" }}>
            <span
              style={{
                position: "absolute",
                left: "0",
                color: "#2563eb",
                fontWeight: 700,
              }}
            >
              •
            </span>
            Not everyone can access chess coaches. We provide a{" "}
            <strong style={{ color: "#2563eb" }}>
              free and accessible platform for aspiring players
            </strong>{" "}
            who are eager to improve their game.
          </li>
        </ul>
      </div>
    </div>
  );
};

export default ImitatorSection;
