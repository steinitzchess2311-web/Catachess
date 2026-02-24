import React from "react";
import PageTransition from "../../components/animation/PageTransition";
import HeroSection from "./HeroSection";
import FundingPlansSection from "./FundingPlansSection";

const SponsorshipPage = () => {
  return (
    <PageTransition>
      <div
        style={{
          padding: "40px 24px 70px",
          fontFamily: "var(--font-family)",
          background: "var(--bg-app)",
          minHeight: "calc(100vh - 100px)",
          overflowY: "auto",
        }}
      >
        <div
          style={{
            maxWidth: "1100px",
            margin: "0 auto",
          }}
        >
          <HeroSection />
          <FundingPlansSection />
        </div>
      </div>
    </PageTransition>
  );
};

export default SponsorshipPage;
