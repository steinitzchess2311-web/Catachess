import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import type { WorkspaceMode } from "@ui/modules/workspace/events/types";
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
import { HomePage } from "./pages/home";
import { TerminalLauncher } from "@patch/modules/terminal";
import { createCataMazeCommand } from "@patch/modules/catamaze";
import { CatPet } from "@patch/modules/cats";
import { UserContext } from "./contexts/UserContext";
import "@patch/styles/index.css";

const AboutPage = React.lazy(() => import("./pages/aboutPage/AboutPage"));
const BlogsPage = React.lazy(() => import("./pages/BlogsPage"));
const SponsorshipPage = React.lazy(() => import("./pages/SponsorshipPage/SponsorshipPage"));
const TranslatePage = React.lazy(() => import("./pages/translate"));
const PlayersIndex = React.lazy(() => import("@patch/modules/player/PlayerPage"));
const PlayerDetail = React.lazy(() => import("@patch/modules/tagger/pages/PlayerDetail"));
const PatchStudyPage = React.lazy(() => import("@patch/PatchStudyPage").then(m => ({ default: m.PatchStudyPage })));
const GameViewerPage = React.lazy(() => import("@patch/game/GameViewerPage").then(m => ({ default: m.GameViewerPage })));
const BoardEditorPage = React.lazy(() => import("@patch/modules/board_editor").then(m => ({ default: m.BoardEditorPage })));
const AnalysisPage = React.lazy(() => import("./pages/analysis/AnalysisPage").then(m => ({ default: m.AnalysisPage })));
const PlayPage = React.lazy(() => import("@patch/modules/user_games").then(m => ({ default: m.PlayPage })));
const LiveGamePage = React.lazy(() => import("@patch/modules/user_games").then(m => ({ default: m.LiveGamePage })));
const AnalyzeGamePage = React.lazy(() => import("@patch/modules/user_games").then(m => ({ default: m.AnalyzeGamePage })));
const JoinGamePage = React.lazy(() => import("@patch/modules/user_games").then(m => ({ default: m.JoinGamePage })));

// Entry switch configuration: default to patch unless explicitly disabled
const USE_PATCH_STUDY = import.meta.env.VITE_USE_PATCH_STUDY !== "false";

function toSlug(title: string): string {
  return title.replace(/\s+/g, '-');
}

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
    return params.get("redirect") || "/workspace/private";
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

function WorkspaceSelect({ mode }: { mode: WorkspaceMode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  // useNavigate() recreates its function on every URL change (it depends on useLocation internally).
  // Storing it in a ref means callbacks always have the latest navigate without triggering re-init.
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";
    // Re-read the current URL when the effect runs (mode prop changed = new route).
    const currentPath = window.location.pathname;
    const currentSearch = window.location.search;
    const parentId = new URLSearchParams(currentSearch).get("parent") || undefined;
    // path: /workspace/{mode}/{topFolderSlug?}
    // parts: ['workspace', mode, topFolderSlug?]
    const parts = currentPath.split("/").filter(Boolean);
    const topFolderSlug = parts.length >= 3 ? decodeURIComponent(parts[2]) : undefined;

    initWorkspace(containerRef.current, {
      initialMode: mode,
      initialParentId: parentId,
      initialTopFolderName: topFolderSlug,
      onWorkspaceNavigate: (newMode, topFolder) => {
        const base = `/workspace/${newMode}`;
        const next = topFolder ? `${base}/${toSlug(topFolder)}` : base;
        if (window.location.pathname !== next) {
          navigateRef.current(next, { replace: true });
        }
      },
      onOpenStudy: (studyId, context) => {
        const base = `/workspace/${context.mode}`;
        const next = context.topFolder
          ? `${base}/${toSlug(context.topFolder)}/${studyId}`
          : `/${studyId}`;
        window.location.href = next;
      },
    });

    // When not logged in on private/shared workspace:
    // 1. Inject a guest banner into #test-sign-container (below the sort bar)
    // 2. Disable the New Folder / New Study cards
    let observer: MutationObserver | null = null;
    if ((mode === "private" || mode === "shared") && !isAuthed()) {
      const loginHref = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;

      const applyGuestUI = (root: HTMLElement) => {
        // Inject banner into #test-sign-container if not already done
        const signContainer = root.querySelector<HTMLElement>("#test-sign-container");
        if (signContainer && !signContainer.querySelector(".guest-banner")) {
          const banner = document.createElement("div");
          banner.className = "guest-banner";
          banner.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #fdf8ee 0%, #f7edcc 100%);
            border-left: 4px solid #c9a84c;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 0 0 var(--space-md, 16px) 0;
            box-shadow: 0 2px 8px rgba(180,140,60,0.12);
            font-size: 15px;
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            color: #7a5c1e;
          `;
          banner.innerHTML = `
            <span>Log in to create folders or studies.</span>
            <a href="${loginHref}" style="color:#b07d20;font-weight:700;text-decoration:none;border-bottom:1px solid #b07d20;padding-bottom:1px;">Log in →</a>
          `;
          signContainer.appendChild(banner);
        }
        // Disable new-item-cards
        root.querySelectorAll<HTMLElement>(".new-item-card").forEach((card) => {
          card.style.opacity = "0.35";
          card.style.pointerEvents = "none";
          card.style.cursor = "not-allowed";
        });
      };

      observer = new MutationObserver(() => {
        if (containerRef.current) applyGuestUI(containerRef.current);
      });
      observer.observe(containerRef.current, { childList: true, subtree: true });
    }

    return () => {
      observer?.disconnect();
    };
  }, [mode]); // ONLY depend on mode — navigate is accessed via ref to avoid spurious re-inits

  return (
    <div>
      <div style={{ display: "none" }} dangerouslySetInnerHTML={{ __html: workspaceLayout }} />
      <div ref={containerRef} />
    </div>
  );
}

const AccountPage = React.lazy(() => import("../AccountPage"));
const PublicProfilePage = React.lazy(() => import("@patch/modules/user_profile").then(m => ({ default: m.PublicProfilePage })));
const EditProfilePage = React.lazy(() => import("@patch/modules/user_profile").then(m => ({ default: m.EditProfilePage })));

// ─── Chunk-load resilience ────────────────────────────────────────────────────

function isChunkLoadError(error: Error): boolean {
  const msg = error?.message ?? '';
  return (
    /Failed to fetch dynamically imported module/.test(msg) ||
    /Importing a module script failed/.test(msg) ||
    /Loading chunk \d+ failed/.test(msg) ||
    error.name === 'ChunkLoadError'
  );
}

class ChunkErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(error: Error): void {
    if (!isChunkLoadError(error)) return;
    try {
      const key = `__ckr_${window.location.pathname}__`;
      if (!sessionStorage.getItem(key)) {
        sessionStorage.setItem(key, '1');
        window.location.reload();
      }
    } catch { /* sessionStorage unavailable */ }
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', minHeight: '60vh', gap: '12px', color: '#888',
      }}>
        <span style={{ fontSize: '14px' }}>Failed to load page</span>
        <button
          type="button"
          onClick={() => {
            try { sessionStorage.removeItem(`__ckr_${window.location.pathname}__`); } catch {}
            window.location.reload();
          }}
          style={{
            padding: '6px 18px', border: '1px solid #888', borderRadius: '6px',
            background: 'none', cursor: 'pointer', fontSize: '13px', color: '#888',
          }}
        >
          Refresh page
        </button>
      </div>
    );
  }
}

function PageLoadingFallback() {
  return (
    <>
      <style>{`@keyframes _ck_bar{0%{left:-40%}100%{left:110%}}`}</style>
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0,
        height: '2px', zIndex: 9999, overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: 0, height: '100%', width: '40%',
          background: 'linear-gradient(90deg, transparent, #818cf8, transparent)',
          animation: '_ck_bar 1.1s ease-in-out infinite',
        }} />
      </div>
      <div style={{ minHeight: 'calc(100vh - 60px)' }} />
    </>
  );
}

// RR v6 不支持 /@:username 这种前缀动态段，所以 /@xxx 会命中 /:id。
// 这里统一处理：UUID → 棋谱页（需登录），@username → 公开资料页，其余 → null
function DynamicIdRoute({ currentUsername }: { currentUsername: string | null }) {
  const { id } = useParams<{ id: string }>();
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (id && UUID_RE.test(id)) {
    return <Protected><PatchStudyPage /></Protected>;
  }
  if (id?.startsWith('@')) {
    return <PublicProfilePage currentUsername={currentUsername} />;
  }
  return null;
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
  const [userId, setUserId] = useState<string | null>(null);
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
          setUserId(response.id || null);
        } catch (error) {
          console.error("Failed to fetch user profile:", error);
        }
      }
    };
    fetchUser();
  }, [authed]);

  return (
    <UserContext.Provider value={{ username, userRole, userId }}>
      <Header username={username} isAuthed={authed} userRole={userRole} />
      <main>
        <ChunkErrorBoundary key={location.pathname}>
        <Suspense fallback={<PageLoadingFallback />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/blogs" element={<BlogsPage />} />
          <Route path="/blogs/:articleId" element={<BlogsPage />} />
          <Route path="/sponsorship" element={<SponsorshipPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/board-editor" element={<BoardEditorPage />} />
          <Route path="/translate" element={<TranslatePage />} />
          <Route path="/players"      element={<PlayersIndex />} />
          <Route path="/players/:name" element={<PlayersIndex />} />
          <Route
            path="/players1/:id"
            element={
              <Protected>
                <PlayerDetail />
              </Protected>
            }
          />
          {/* Legacy workspace-select redirect */}
          <Route path="/workspace-select" element={<Navigate to="/workspace/private" replace />} />

          {/* Study routes — must precede workspace wildcard */}
          <Route path="/workspace/private/:topFolder/:id" element={<PatchStudyPage />} />
          <Route path="/workspace/public/:topFolder/:id" element={<PatchStudyPage />} />
          <Route path="/workspace/shared/:topFolder/:id" element={<PatchStudyPage />} />

          {/* Workspace browser — wildcard covers /workspace/{mode} and /workspace/{mode}/{topFolder} */}
          <Route path="/workspace/private/*" element={<WorkspaceSelect mode="private" />} />
          <Route path="/workspace/public/*" element={<WorkspaceSelect mode="public" />} />
          <Route path="/workspace/shared/*" element={<WorkspaceSelect mode="shared" />} />

          {/* /workspace → redirect based on auth state */}
          <Route path="/workspace" element={<Navigate to={isAuthed() ? "/workspace/private" : "/workspace/public"} replace />} />

          {/* Legacy study routes (backward compat) */}
          <Route path="/workspace/:id" element={<Protected>{USE_PATCH_STUDY ? <PatchStudyPage /> : <WorkspacePage />}</Protected>} />
          <Route path="/patch/workspace/:id" element={<Protected><PatchStudyPage /></Protected>} />

          {/* Games — 大厅 + 实时对局 + 加入 + 赛后分析 */}
          <Route path="/play" element={<PlayPage username={username} />} />
          <Route path="/chess/:gameId/join" element={<JoinGamePage username={username} />} />
          <Route path="/chess/:gameId/analyze" element={<AnalyzeGamePage />} />
          <Route path="/chess/:gameId" element={<LiveGamePage username={username} />} />

          {/* Game viewer — must precede the /:id catch-all */}
          <Route path="/game/:id" element={<GameViewerPage />} />

          {/* 用户设置（编辑资料）— 需登录 */}
          <Route path="/settings" element={<Protected><EditProfilePage currentUsername={username} /></Protected>} />

          {/* /:id — UUID → 棋谱页（需登录），@username → 公开资料页（无需登录）
               RR v6 不支持 /@:username 形式，需在组件内分流 */}
          <Route path="/:id" element={<DynamicIdRoute currentUsername={username} />} />

          <Route path="*" element={<div>404</div>} />
        </Routes>
        </Suspense>
        </ChunkErrorBoundary>
      </main>
      <Footer />
      <TerminalLauncher customCommands={[catamazeCommand]} />
      {ENABLE_CAT_PET && showCat && <CatPet initialPosition={catInitialPosition} />}
    </UserContext.Provider>
  );
}


export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
