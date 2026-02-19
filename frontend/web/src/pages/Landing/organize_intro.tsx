import React from "react";
import { Link } from "react-router-dom";
import organizeIntroImage from "../../assets/photos/organize_intro.jpg";

const OrganizeIntro = () => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "40% 1fr",
        gap: "0",
        alignItems: "center",
        padding: "50px",
        border: "2px solid transparent",
        boxSizing: "border-box",
      }}
    >
      {/* Left: Image square */}
      <div
        style={{
          border: "2px solid transparent",
          width: "100%",
          aspectRatio: "1 / 1",
          justifySelf: "center",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <img
          src={organizeIntroImage}
          alt="Organize your chess materials"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>

      {/* Right: Text content (right-aligned) */}
      <div
        style={{
          border: "2px solid transparent",
          height: "100%",
          padding: "35px 40px 35px 0",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: "45px",
        }}
      >
        <div
          style={{
            fontSize: "40px",
            fontWeight: 700,
            lineHeight: 1.2,
            textAlign: "right",
          }}
        >
          Freely Organize Your Chess Materials!
        </div>
        <div
          style={{
            fontSize: "18px",
            lineHeight: 1.6,
            color: "#2f2a26",
            textAlign: "right",
          }}
        >
          We serve as your FREE online ChessBase
          <br />
          that allows you to effectively organize your chess materials!
        </div>
        <Link
          to="/private"
          className="landing-button"
          style={{
            alignSelf: "flex-end",
            backgroundColor: "#1A73E8",
            border: "2px solid #1A73E8",
            borderRadius: "8px",
            padding: "14px 28px",
            fontSize: "18px",
            fontWeight: 600,
            color: "white",
            textDecoration: "none",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "#1A73E8";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#1A73E8";
            e.currentTarget.style.color = "white";
          }}
        >
          Get Started for Free
        </Link>
      </div>
    </div>
  );
};

export default OrganizeIntro;
