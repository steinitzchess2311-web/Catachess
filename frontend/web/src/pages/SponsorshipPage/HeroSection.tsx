import React from "react";

const HeroSection = () => {
  return (
    <div
      style={{
        textAlign: "center",
        marginBottom: "50px",
      }}
    >
      <h1
        style={{
          fontSize: "2.25rem",
          fontWeight: 800,
          color: "#0f172a",
          marginBottom: "12px",
          letterSpacing: "0.4px",
        }}
      >
        SPONSORSHIP
      </h1>
      <p
        style={{
          fontSize: "1.05rem",
          fontWeight: 500,
          color: "#475569",
          marginBottom: "0",
        }}
      >
        Your help makes chess training more accessible to all!
      </p>
    </div>
  );
};

export default HeroSection;
