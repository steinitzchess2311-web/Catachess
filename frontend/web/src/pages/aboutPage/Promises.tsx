import React from "react";

const Promises = () => {
  const promises = [
    {
      title: "No Violation of rights:",
      description:
        "Your imported games would not be confidential to the third party.",
      icon: "🎁",
    },
    {
      title: "No forced premium plans:",
      description:
        "Our core basic model remains free and accessible to all. However, donars and premium members can choose an application/desktop pet to accompany your learning.",
      icon: "🚫",
    },
    {
      title: "No neglected voices:",
      description:
        "Beta testers are more than welcome to send user feedback to info@steinitzchess.org. We will carefully go over each suggestion.",
      icon: "💡",
    },
  ];

  return (
    <div
      style={{
        marginBottom: "60px",
        padding: "40px 0",
      }}
    >
      {/* Header */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "45px",
        }}
      >
        <h2
          style={{
            fontSize: "2rem",
            fontWeight: 700,
            color: "#0f172a",
            marginBottom: "16px",
            lineHeight: "1.4",
          }}
        >
          Our Three NOs.
        </h2>
      </div>

      {/* Promise Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "28px",
          maxWidth: "1100px",
          margin: "0 auto",
        }}
      >
        {promises.map((promise, index) => (
          <div
            key={index}
            style={{
              background: "rgba(255, 255, 255, 0.95)",
              borderRadius: "16px",
              padding: "20px 24px",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
              transition: "transform 0.3s ease, box-shadow 0.3s ease",
              border: "1px solid rgba(37, 99, 235, 0.1)",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-4px)";
              e.currentTarget.style.boxShadow = "0 8px 30px rgba(37, 99, 235, 0.12)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.08)";
            }}
          >
            {/* Title */}
            <h3
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "#2563eb",
                marginBottom: "8px",
                lineHeight: "1.4",
                textAlign: "center",
              }}
            >
              {promise.title}
            </h3>

            {/* Description */}
            <p
              style={{
                fontSize: "1rem",
                lineHeight: "1.7",
                color: "#475569",
                margin: "0",
                textAlign: "center",
              }}
            >
              {promise.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Promises;
