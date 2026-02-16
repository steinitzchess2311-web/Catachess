import React from "react";
import { Link } from "react-router-dom";
import { EnvelopeClosedIcon, GlobeIcon, ChatBubbleIcon } from "@radix-ui/react-icons";
import "./Footer.css";

const Footer: React.FC = () => {
  return (
    <footer className="app-footer">
      <div className="footer-gradient-overlay"></div>
      <div className="footer-content">
        <div className="footer-section footer-main">
          <div className="footer-brand">
            <div className="brand-icon">♔</div>
            <div className="brand-text">
              <p className="brand-title">Developed by</p>
              <p className="brand-names">Quanhao Li & Jorlanda Chen</p>
            </div>
          </div>
        </div>

        <div className="footer-section footer-contact">
          <h3 className="footer-heading">Contact</h3>
          <div className="contact-item">
            <EnvelopeClosedIcon className="contact-icon" />
            <a href="mailto:info@steinitzchess.org" className="contact-link">
              info@steinitzchess.org
            </a>
          </div>
          <div className="contact-item">
            <ChatBubbleIcon className="contact-icon" />
            <span className="contact-label">WeChat ID:</span>
            <span className="contact-text">Cata-Dragon</span>
          </div>
          <div className="contact-item">
            <GlobeIcon className="contact-icon" />
            <a
              href="https://steinitzchess.org"
              target="_blank"
              rel="noopener noreferrer"
              className="contact-link"
            >
              steinitzchess.org
            </a>
          </div>
        </div>

        <div className="footer-section footer-appreciation">
          <h3 className="footer-heading">Appreciated Individuals</h3>
          <div className="appreciation-grid">
            <span className="appreciation-name">Cata Long</span>
            <span className="appreciation-name">Jorlanda Chen</span>
            <span className="appreciation-name">Yiping Lou</span>
            <span className="appreciation-name">Zhian Chen</span>
            <span className="appreciation-name">Liren Ding</span>
            <span className="appreciation-name">Yaochen Yu</span>
            <span className="appreciation-name">ZiFei Luo</span>
            <span className="appreciation-name">Yuxuan Zheng</span>
            <span className="appreciation-name">Ziyang Huang</span>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="footer-divider"></div>
        <div className="footer-links">
          <Link to="/about" className="footer-link">About</Link>
        </div>
        <p className="footer-copyright">
          Developed by Quanhao (CataDragon) and Jorlanda (Chestnut).
        </p>
      </div>
    </footer>
  );
};

export default Footer;
