/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * OfficialSection component - official blog category group.
 */

import React from "react";
import pureLogo from "../../../assets/chessortag_pure_logo.png";
import { ChevronDownIcon } from "@radix-ui/react-icons";
import { OfficialSectionProps } from "./types";

const OfficialSection: React.FC<OfficialSectionProps> = ({
  activeCategory,
  isOfficialOpen,
  setIsOfficialOpen,
  onCategoryClick,
}) => {
  const officialSubItems = [
    { id: "about", label: "Our Stories" },
    { id: "function", label: "Functions Intro" },
    { id: "devlog", label: "Developer Logs" },
  ];

  const isOfficialRootActive = activeCategory === undefined || activeCategory === 'allblogs' || activeCategory === 'official';

  return (
    <div className="blog-sidebar-section">
      <button
        type="button"
        onClick={() => {
          onCategoryClick('allblogs');
          setIsOfficialOpen((prev) => !prev);
        }}
        className={`blog-sidebar-item blog-sidebar-item--official${isOfficialRootActive ? ' is-active' : ''}`}
      >
        <img
          src={pureLogo}
          alt="Chessortag"
          className="blog-sidebar-item__logo"
        />
        <span className="blog-sidebar-item__label">Chessortag Official</span>
        <ChevronDownIcon
          width={18}
          height={18}
          className={`blog-sidebar-item__chevron${isOfficialOpen ? ' is-open' : ''}`}
        />
      </button>

      <div
        className={`blog-sidebar-sublist${isOfficialOpen ? ' is-open' : ''}`}
      >
        {officialSubItems.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onCategoryClick(item.id)}
            className={`blog-sidebar-subitem${activeCategory === item.id ? ' is-active' : ''}`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default OfficialSection;
