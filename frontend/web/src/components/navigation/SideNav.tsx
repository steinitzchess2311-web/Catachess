import React, { useState, useEffect } from "react";
import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronLeftIcon, ChevronRightIcon } from "@radix-ui/react-icons";

interface NavItem {
  id: string;
  label: string;
  icon?: string;
}

interface SideNavProps {
  items: NavItem[];
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const SideNav: React.FC<SideNavProps> = ({ items, isOpen: controlledIsOpen, onOpenChange }) => {
  const [activeSection, setActiveSection] = useState<string>(items[0]?.id || "");
  const [internalIsOpen, setInternalIsOpen] = useState<boolean>(true);

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const setIsOpen = onOpenChange || setInternalIsOpen;

  useEffect(() => {
    const handleScroll = () => {
      const sections = items.map((item) => document.getElementById(item.id));
      const scrollPosition = window.scrollY + 150; // Offset for header

      for (let i = sections.length - 1; i >= 0; i--) {
        const section = sections[i];
        if (section && section.offsetTop <= scrollPosition) {
          setActiveSection(items[i].id);
          break;
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll(); // Initial check

    return () => window.removeEventListener("scroll", handleScroll);
  }, [items]);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      const yOffset = -120; // Offset for header
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: "smooth" });
    }
  };

  return (
    <Collapsible.Root open={isOpen} onOpenChange={setIsOpen}>
      <nav
        style={{
          position: "fixed",
          top: "96px",
          left: "max(24px, calc((100vw - 1400px) / 2))",
          width: isOpen ? "220px" : "60px",
          background: "rgba(255, 255, 255, 0.96)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: isOpen ? "24px 0" : "16px 0",
          boxShadow: "var(--shadow-1)",
          backdropFilter: "blur(10px)",
          zIndex: 100,
          transition: "width 0.3s ease, padding 0.3s ease",
        }}
      >
        {/* Toggle Button */}
        <Collapsible.Trigger asChild>
          <button
            style={{
              position: "absolute",
              top: "12px",
              right: "12px",
              width: "32px",
              height: "32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "none",
              background: "rgba(37, 99, 235, 0.08)",
              borderRadius: "6px",
              cursor: "pointer",
              color: "#2563eb",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(37, 99, 235, 0.16)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(37, 99, 235, 0.08)";
            }}
          >
            {isOpen ? <ChevronLeftIcon width={20} height={20} /> : <ChevronRightIcon width={20} height={20} />}
          </button>
        </Collapsible.Trigger>

        {/* Collapsed State - Just Icons */}
        {!isOpen && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
              marginTop: "48px",
            }}
          >
            {items.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  title={item.label}
                  style={{
                    width: "40px",
                    height: "40px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    border: "none",
                    background: isActive ? "rgba(37, 99, 235, 0.12)" : "transparent",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "1.3rem",
                    transition: "all 0.2s ease",
                    borderLeft: isActive ? "3px solid #2563eb" : "3px solid transparent",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = "rgba(37, 99, 235, 0.08)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  {item.icon}
                </button>
              );
            })}
          </div>
        )}

        {/* Expanded State - Full Navigation */}
        <Collapsible.Content>
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              marginTop: "48px",
            }}
          >
            {items.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <li key={item.id} style={{ marginBottom: "4px" }}>
                  <button
                    onClick={() => scrollToSection(item.id)}
                    style={{
                      width: "100%",
                      padding: "12px 20px",
                      border: "none",
                      background: "transparent",
                      textAlign: "left",
                      cursor: "pointer",
                      fontSize: "0.95rem",
                      color: isActive ? "#2563eb" : "#475569",
                      fontWeight: isActive ? 600 : 500,
                      transition: "all 0.3s ease",
                      position: "relative",
                      borderLeft: isActive ? "3px solid #2563eb" : "3px solid transparent",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.color = "#2563eb";
                        e.currentTarget.style.transform = "translateX(4px)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.color = "#475569";
                        e.currentTarget.style.transform = "translateX(0)";
                      }
                    }}
                  >
                    {item.icon && <span style={{ fontSize: "1.1rem" }}>{item.icon}</span>}
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </Collapsible.Content>
      </nav>
    </Collapsible.Root>
  );
};

export default SideNav;
