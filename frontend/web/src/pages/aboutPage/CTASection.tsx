import React from "react";


const CTASection = () => {

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
        borderRadius: "16px",
        padding: "45px",
        textAlign: "center",
        boxShadow: "0 8px 32px rgba(139, 115, 85, 0.3)",
      }}
    >
      <h2
        style={{
          fontSize: "2.3rem",
          fontWeight: 800,
          color: "white",
          marginBottom: "20px",
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        YOUR HELP IS EXTREMELY CRUCIAL TO US!
      </h2>
      <p
        style={{
          fontSize: "1.15rem",
          color: "rgba(255, 255, 255, 0.95)",
          marginBottom: "28px",
          lineHeight: "1.7",
        }}
      >
        Contact us at <strong>info@steinitzchess.org</strong> for sponsorship inquiries
      </p>
      <a
        href="mailto:info@steinitzchess.org"
        style={{
          display: "inline-block",
          background: "white",
          color: "#2563eb",
          padding: "14px 42px",
          borderRadius: "50px",
          fontSize: "1.05rem",
          fontWeight: 700,
          textDecoration: "none",
          boxShadow: "0 6px 20px rgba(0, 0, 0, 0.15)",
          transition: "transform 0.2s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-2px)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
        }}
      >
        Contact Us
      </a>
    </div>
  );
};

export default CTASection;
