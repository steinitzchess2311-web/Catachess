import React from "react";

const Developer = () => {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: "100%",
        borderRadius: "20px",
        border: "1px solid rgba(26, 27, 31, 0.12)",
        background: "rgba(255, 255, 255, 0.7)",
        boxShadow: "0 16px 36px rgba(28, 23, 18, 0.1)",
        padding: "22px",
        display: "grid",
        gridTemplateColumns:
          "minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)",
        alignItems: "center",
        gap: "18px",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
          minWidth: 0,
        }}
      >
        <img
          src="/assets/developers/CataDragon.png"
          alt="CataDragon"
          loading="eager"
          style={{
            width: "100%",
            maxWidth: "180px",
            height: "auto",
            display: "block",
            objectFit: "contain",
          }}
        />
        <div style={{ fontSize: "14px", fontWeight: 600, color: "#0f172a" }}>
          CataDragon
        </div>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          fontSize: "20px",
          lineHeight: 1.7,
          color: "#0f172a",
        }}
      >
        CataDragon is the co-developer of this website. He loves playing Clash Royale.
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
          minWidth: 0,
        }}
      >
        <img
          src="/assets/developers/ChessNut.jpg"
          alt="ChessNut"
          loading="eager"
          style={{
            width: "100%",
            maxWidth: "180px",
            height: "auto",
            display: "block",
            objectFit: "contain",
          }}
        />
        <div style={{ fontSize: "14px", fontWeight: 600, color: "#0f172a" }}>
          ChessNut
        </div>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          fontSize: "20px",
          lineHeight: 1.7,
          color: "#0f172a",
        }}
      >
        ChessNut is the co-developer of this website. She has a cat named nut.
      </div>
    </div>
  );
};

export default Developer;
