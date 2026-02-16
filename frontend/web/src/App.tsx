import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api } from "@ui/assets/api";
import { initSignup } from "@ui/modules/auth/signup/events/index";
import { initWorkspace } from "@ui/modules/workspace/events/index";
import { initStudy } from "@ui/modules/study/events/index";
import "@ui/assets/variables.css";
import "@ui/modules/auth/login/styles/index.css";
import "@ui/modules/auth/signup/styles/index.css";
import "@ui/modules/workspace/styles/index.css";
import "@ui/modules/study/styles/index.css";
import "@ui/modules/discussion/styles/index.css";
import workspaceLayout from "@ui/modules/workspace/layout/index.html?raw";
import studyLayout from "@ui/modules/study/layout/index.html?raw";
import discussionLayout from "@ui/modules/discussion/layout/index.html?raw";
import signupLayout from "@ui/modules/auth/signup/layout/index.html?raw";
import Header from "./components/header/Header";
import Footer from "./components/footer/Footer";
import TestSign from "./components/dialogBox/TestSign";
import AboutPage from "./pages/aboutPage/AboutPage";
import BlogsPage from "./pages/BlogsPage";
import ArticleDetailPage from "./pages/BlogsPage/ArticleDetailPage";
import SponsorshipPage from "./pages/SponsorshipPage/SponsorshipPage";
import LandingPage from "./pages/Landing/LandingPage";
import { HomePage } from "./pages/home";
import TranslatePage from "./pages/translate";
import PlayersIndex from "@patch/modules/tagger/pages/PlayersIndex";
import PlayerDetail from "@patch/modules/tagger/pages/PlayerDetail";
import AccountPage from "../AccountPage";
import { PatchStudyPage } from "@patch/PatchStudyPage";
import { TerminalLauncher } from "@patch/modules/terminal";
import { createCataMazeCommand } from "@patch/modules/catamaze";
import { CatPet } from "@patch/modules/cats";
import "@patch/styles/index.css";

// Entry switch configuration: default to patch unless explicitly disabled
const USE_PATCH_STUDY = import.meta.env.VITE_USE_PATCH_STUDY !== "false";

// Cat pet feature toggle
const ENABLE_CAT_PET = false;

const TOKEN_KEY = "catachess_token";
const USER_ID_KEY = "catachess_user_id";

function readStored(key: string) {
  return localStorage.getItem(key) || sessionStorage.getItem(key);
}

function decodeTokenPayload(token: string | null) {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) base64 += "=";
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

function decodeUserIdFromToken(token: string | null) {
  const payload = decodeTokenPayload(token);
  return payload && typeof payload.sub === "string" ? payload.sub : null;
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_ID_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_ID_KEY);
}

function isTokenValid(token: string | null) {
  if (!token) return false;
  const payload = decodeTokenPayload(token);
  if (!payload) return false;
  if (typeof payload.exp !== "number") return true;
  return payload.exp * 1000 > Date.now();
}

function ensureUserId(token: string | null) {
  const existing = readStored(USER_ID_KEY);
  if (existing) return existing;
  const derived = decodeUserIdFromToken(token);
  if (derived) {
    localStorage.setItem(USER_ID_KEY, derived);
    return derived;
  }
  return null;
}

function isAuthed() {
  const token = readStored(TOKEN_KEY);
  if (!isTokenValid(token)) {
    clearAuth();
    return false;
  }
  const userId = readStored(USER_ID_KEY) || ensureUserId(token);
  return Boolean(userId);
}

function Protected({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  if (!isAuthed()) {
    return (
      <Navigate
        to={`/login?redirect=${encodeURIComponent(
          location.pathname + location.search
        )}`}
        replace
      />
    );
  }
  return <>{children}</>;
}

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const redirect = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("redirect") || "/workspace-select";
  }, [location.search]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login/json", {
        identifier: email,
        password,
      });

      if (response?.access_token) {
        localStorage.setItem(TOKEN_KEY, response.access_token);
        const userId = decodeUserIdFromToken(response.access_token);
        if (userId) {
          localStorage.setItem(USER_ID_KEY, userId);
        }
        window.location.replace(redirect);
      } else {
        setError("Invalid login response.");
      }
    } catch (err: any) {
      setError(err?.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <TestSign floating={true} />
      <div className="login-container">
        <div className="login-card">
          <h1 className="login-title">Sign In</h1>
          <form id="login-form" onSubmit={submit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                required
                placeholder="Enter your email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                required
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <div id="login-error" className="error-message">
              {error}
            </div>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Signing In..." : "Sign In"}
            </button>
          </form>
          <div className="login-footer">
            <p>
              Don&apos;t have an account? <Link to="/signup">Sign up</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

function SignupPage() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";
    initSignup(containerRef.current);
  }, []);

  return (
    <div>
      <div style={{ display: "none" }} dangerouslySetInnerHTML={{ __html: signupLayout }} />
      <div ref={containerRef} />
    </div>
  );
}

function WorkspaceSelect() {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const initialParentId = searchParams.get("parent") || "root";
  const resetWorkspace = (location.state as { resetWorkspace?: number } | null)?.resetWorkspace;

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";
    initWorkspace(containerRef.current, {
      onOpenStudy: (studyId) => {
        // Use patch route if VITE_USE_PATCH_STUDY is enabled
        const basePath = USE_PATCH_STUDY ? "/patch/workspace" : "/workspace";
        navigate(`${basePath}/${studyId}`);
      },
      initialParentId,
    });
  }, [navigate, initialParentId, resetWorkspace]);

  return (
    <div>
      <div style={{ display: "none" }} dangerouslySetInnerHTML={{ __html: workspaceLayout }} />
      <div ref={containerRef} />
    </div>
  );
}

function WorkspacePage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { id } = useParams();

  useEffect(() => {
    if (!containerRef.current || !id) return;
    let disposed = false;
    let boardInstance: { destroy?: () => void } | null = null;
    containerRef.current.innerHTML = "";

    const start = async () => {
      try {
        boardInstance = await initStudy(containerRef.current!, id);
        if (disposed && boardInstance?.destroy) {
          boardInstance.destroy();
        }
      } catch (error) {
        console.error("Failed to init study:", error);
      }
    };

    start();

    return () => {
      disposed = true;
      if (boardInstance?.destroy) {
        boardInstance.destroy();
      }
    };
  }, [id]);

  return (
    <div>
      <div
        style={{ display: "none" }}
        dangerouslySetInnerHTML={{ __html: studyLayout + discussionLayout }}
      />
      <div ref={containerRef} />
    </div>
  );
}

function Layout() {
  const location = useLocation();
  const [username, setUsername] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [showCat, setShowCat] = useState(false);
  const authed = isAuthed();
  const catamazeStateRef = useRef({
    gameId: null as string | null,
    observation: null as any,
    queueSize: 0,
  });
  const catamazeCommand = useMemo(
    () => createCataMazeCommand(catamazeStateRef),
    []
  );

  // Check if landing intro animation has completed
  useEffect(() => {
    if (location.pathname === '/') {
      // On landing page, check if intro has been shown
      const introShown = sessionStorage.getItem("landingIntroShown");
      if (introShown === "true") {
        // Intro already shown, show cat immediately
        setShowCat(true);
      } else {
        // Wait for intro to complete (1200ms animation duration)
        setShowCat(false);
        const timer = setTimeout(() => {
          setShowCat(true);
        }, 1300);
        return () => clearTimeout(timer);
      }
    } else {
      // On other pages, show cat immediately
      setShowCat(true);
    }
  }, [location.pathname]);

  // Calculate cat initial position based on current route
  const catInitialPosition = useMemo(() => {
    if (location.pathname === '/') {
      // Landing page - position cat below "Join" text
      // "Join" is at the beginning of the right-aligned title
      return {
        x: typeof window !== 'undefined' ? window.innerWidth * 0.49 : 850,
        y: typeof window !== 'undefined' ? window.innerHeight * 0.51 : 510,
      };
    }
    // Default position for all other pages (bottom left)
    return undefined; // Let CatPet use its default
  }, [location.pathname]);

  useEffect(() => {
    const fetchUser = async () => {
      if (authed) {
        try {
          const token = readStored(TOKEN_KEY);
          const derivedName = decodeUserIdFromToken(token) || readStored(USER_ID_KEY);
          if (derivedName) {
            setUsername(derivedName);
          }
          const response = await api.request("/user/profile", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          setUsername(response.username);
          setUserRole(response.role || null);
        } catch (error) {
          console.error("Failed to fetch user profile:", error);
        }
      }
    };
    fetchUser();
  }, [authed]);

  return (
    <>
      <Header username={username} isAuthed={authed} userRole={userRole} />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/blogs" element={<BlogsPage />} />
          <Route path="/blogs/:articleId" element={<BlogsPage />} />
          <Route path="/sponsorship" element={<SponsorshipPage />} />
          <Route path="/translate" element={<TranslatePage />} />
          <Route
            path="/players"
            element={
              <Protected>
                <PlayersIndex />
              </Protected>
            }
          />
          <Route
            path="/players/:id"
            element={
              <Protected>
                <PlayerDetail />
              </Protected>
            }
          />
          <Route
            path="/workspace-select"
            element={
              <Protected>
                <WorkspaceSelect />
              </Protected>
            }
          />
          <Route
            path="/workspace/:id"
            element={
              <Protected>
                {USE_PATCH_STUDY ? <PatchStudyPage /> : <WorkspacePage />}
              </Protected>
            }
          />
          {/* Patch-based study route - explicit route for new implementation */}
          <Route
            path="/patch/workspace/:id"
            element={
              <Protected>
                <PatchStudyPage />
              </Protected>
            }
          />
          <Route
            path="/account"
            element={
              <Protected>
                <AccountPage />
              </Protected>
            }
          />
          <Route path="/workspace" element={<Navigate to="/workspace-select" replace />} />
          <Route path="*" element={<div>404</div>} />
        </Routes>
      </main>
      <Footer />
      <TerminalLauncher customCommands={[catamazeCommand]} />
      {ENABLE_CAT_PET && showCat && <CatPet initialPosition={catInitialPosition} />}
    </>
  );
}


export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
