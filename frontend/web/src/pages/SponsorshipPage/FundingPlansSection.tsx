import React from "react";

const FundingPlansSection = () => {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "24px",
        marginBottom: "60px",
        boxShadow: "var(--shadow-1)",
      }}
    >
      <h2
        style={{
          fontSize: "1.65rem",
          fontWeight: 700,
          color: "#0f172a",
          marginBottom: "20px",
          textAlign: "center",
        }}
      >
        Your funds help us:
      </h2>
      <ul
        style={{
          fontSize: "1rem",
          lineHeight: "1.85",
          color: "#475569",
          paddingLeft: "0",
          listStyleType: "none",
          margin: 0,
        }}
      >
        <li style={{ marginBottom: "16px", display: "flex", alignItems: "flex-start" }}>
          <span
            style={{
              display: "inline-block",
              width: "28px",
              height: "28px",
              background: "#2563eb",
              color: "white",
              borderRadius: "50%",
              textAlign: "center",
              lineHeight: "28px",
              marginRight: "10px",
              flexShrink: 0,
              fontWeight: 700,
              fontSize: "0.9rem",
            }}
          >
            1
          </span>
          Better imitation of our tagged coaches.
        </li>
        <li style={{ marginBottom: "16px", display: "flex", alignItems: "flex-start" }}>
          <span
            style={{
              display: "inline-block",
              width: "28px",
              height: "28px",
              background: "#2563eb",
              color: "white",
              borderRadius: "50%",
              textAlign: "center",
              lineHeight: "28px",
              marginRight: "10px",
              flexShrink: 0,
              fontWeight: 700,
              fontSize: "0.9rem",
            }}
          >
            2
          </span>
          A wider audience: we will reach out to more communities and even our tagged coaches for future support.
        </li>
        <li style={{ marginBottom: "16px", display: "flex", alignItems: "flex-start" }}>
          <span
            style={{
              display: "inline-block",
              width: "28px",
              height: "28px",
              background: "#2563eb",
              color: "white",
              borderRadius: "50%",
              textAlign: "center",
              lineHeight: "28px",
              marginRight: "10px",
              flexShrink: 0,
              fontWeight: 700,
              fontSize: "0.9rem",
            }}
          >
            3
          </span>
          Hold high quality tournaments (see steinitzchess.org) to boost inclusivity among all chess lovers
        </li>
        <li style={{ marginBottom: "16px", display: "flex", alignItems: "flex-start" }}>
          <span
            style={{
              display: "inline-block",
              width: "28px",
              height: "28px",
              background: "#2563eb",
              color: "white",
              borderRadius: "50%",
              textAlign: "center",
              lineHeight: "28px",
              marginRight: "10px",
              flexShrink: 0,
              fontWeight: 700,
              fontSize: "0.9rem",
            }}
          >
            4
          </span>
          <span style={{ textDecoration: "line-through" }}>
            Buy Cat Food and Clash Royale boarding pass
          </span>
        </li>
      </ul>
    </div>
  );
};

export default FundingPlansSection;
