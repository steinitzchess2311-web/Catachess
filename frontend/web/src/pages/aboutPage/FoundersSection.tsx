import React, { useState } from "react";

const FoundersSection = () => {
  const [shakeLeft, setShakeLeft] = useState(false);
  const [shakeRight, setShakeRight] = useState(false);

  const handleLeftClick = () => {
    setShakeLeft(true);
    setTimeout(() => setShakeLeft(false), 500);
  };

  const handleRightClick = () => {
    setShakeRight(true);
    setTimeout(() => setShakeRight(false), 500);
  };

  return (
    <>
      <style>
        {`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
          }
        `}
      </style>
      <div
      style={{
        background: "transparent",
        padding: "32px",
        marginBottom: "60px",
        display: "flex",
        gap: "32px",
        alignItems: "center",
      }}
    >
      <div style={{ flex: "1" }}>
        <p
          style={{
            fontSize: "1.3rem",
            lineHeight: "1.9",
            color: "#4a4a4a",
            marginBottom: "0",
          }}
        >
          This website was conceived, built, and fully developed by two high school students, <strong style={{ color: "#2563eb" }}>Quanhao Li</strong> and{" "}
          <strong style={{ color: "#2563eb" }}>Jorlanda Chen</strong>. As competitive chess players and ambitious young innovators, they created this platform to make high-level chess training more accessible and effective for players everywhere.
        </p>
      </div>
      <div
        style={{
          display: "flex",
          gap: "16px",
          flex: "0 0 auto",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <img
            src="/assets/developers/CataDragon.png"
            alt="Quanhao Li (CataDragon)"
            onClick={handleLeftClick}
            style={{
              width: "120px",
              height: "120px",
              objectFit: "cover",
              borderRadius: "8px",
              boxShadow: "0 3px 10px rgba(0, 0, 0, 0.12)",
              cursor: "pointer",
              animation: shakeLeft ? "shake 0.5s ease-in-out" : "none",
            }}
          />
          <div
            style={{
              fontSize: "0.85rem",
              fontWeight: 600,
              color: "#2563eb",
              textAlign: "center",
            }}
          >
            Quanhao Li
          </div>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <img
            src="/assets/developers/ChessNut.jpg"
            alt="Jorlanda Chen (ChessNut)"
            onClick={handleRightClick}
            style={{
              width: "120px",
              height: "120px",
              objectFit: "cover",
              borderRadius: "8px",
              boxShadow: "0 3px 10px rgba(0, 0, 0, 0.12)",
              cursor: "pointer",
              animation: shakeRight ? "shake 0.5s ease-in-out" : "none",
            }}
          />
          <div
            style={{
              fontSize: "0.85rem",
              fontWeight: 600,
              color: "#2563eb",
              textAlign: "center",
            }}
          >
            Jorlanda Chen
          </div>
        </div>
      </div>
    </div>
    </>
  );
};

export default FoundersSection;
