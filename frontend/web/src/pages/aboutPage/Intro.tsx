import React from "react";

const Intro = () => {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: "100%",
        borderRadius: "20px",
        border: "1px solid rgba(26, 27, 31, 0.12)",
        background: "linear-gradient(145deg, #fff8f0, #efe0d3)",
        boxShadow: "0 18px 40px rgba(28, 23, 18, 0.12)",
        padding: "26px 28px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        boxSizing: "border-box",
      }}
    >
      <div style={{ fontSize: "22px", fontWeight: 700, color: "#0f172a" }}>
        ChessorTag
      </div>
      <div style={{ fontSize: "16px", lineHeight: 1.7, color: "#1a1b1f" }}>
        ChessorTag is a platform that offers:
      </div>
      <ul
        style={{
          margin: 0,
          paddingLeft: "20px",
          fontSize: "16px",
          lineHeight: 1.7,
          color: "#1a1b1f",
          wordBreak: "break-word",
        }}
      >
        <li>
          A detailed report based on your uploaded games, highlighting your weaknesses,
          strengths, and areas of improvement
        </li>
        <li>
          A virtual coach selection of your choice. Players can choose a grandmaster profile
          and learn what move the grandmaster is likely to make in a position. The virtual
          coach can also generate humanized commentary for its choice of move.
        </li>
      </ul>
    </div>
  );
};

export default Intro;
