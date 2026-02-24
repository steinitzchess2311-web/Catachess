import React from "react";
import logoImage from "../../assets/logo.jpg";

interface ArticleModalProps {
  coverImage?: string;
  title: string;
  subtitle: string;
  author?: string;
  date?: string;
  category?: string;
}

const ArticleModal: React.FC<ArticleModalProps> = ({
  coverImage,
  title,
  subtitle,
  author = "Chessortag Team",
  date,
  category,
}) => {
  const displayImage = coverImage || logoImage;

  return (
    <article
      style={{
        background: "rgba(255, 255, 255, 0.9)",
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
        transition: "all 0.3s ease",
        cursor: "pointer",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-4px)";
        e.currentTarget.style.boxShadow = "0 8px 24px rgba(0, 0, 0, 0.12)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "0 2px 12px rgba(0, 0, 0, 0.08)";
      }}
    >
      {/* Cover Image */}
      <div
        style={{
          width: "100%",
          height: "200px",
          overflow: "hidden",
          position: "relative",
          backgroundColor: "#f5f5f5",
        }}
      >
        <img
          src={displayImage}
          alt={title}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transition: "transform 0.3s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
          }}
        />

        {/* Category Badge */}
        {category && (
          <div
            style={{
              position: "absolute",
              top: "12px",
              left: "12px",
              background: "rgba(139, 115, 85, 0.9)",
              color: "white",
              padding: "6px 14px",
              borderRadius: "6px",
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.5px",
              textTransform: "uppercase",
            }}
          >
            {category}
          </div>
        )}
      </div>

      {/* Content */}
      <div
        style={{
          padding: "20px",
          flex: 1,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Title */}
        <h3
          style={{
            fontSize: "1.3rem",
            fontWeight: 700,
            color: "#0f172a",
            marginBottom: "10px",
            lineHeight: "1.4",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {title}
        </h3>

        {/* Subtitle */}
        <p
          style={{
            fontSize: "0.95rem",
            color: "#475569",
            lineHeight: "1.6",
            marginBottom: "16px",
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
            flex: 1,
          }}
        >
          {subtitle}
        </p>

        {/* Footer Meta */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            paddingTop: "12px",
            borderTop: "1px solid rgba(139, 115, 85, 0.1)",
            fontSize: "0.85rem",
            color: "#2563eb",
          }}
        >
          <span style={{ fontWeight: 600 }}>{author}</span>
          {date && (
            <>
              <span style={{ color: "#d0d0d0" }}>•</span>
              <span>{date}</span>
            </>
          )}
        </div>
      </div>
    </article>
  );
};

export default ArticleModal;
