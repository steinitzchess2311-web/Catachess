import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { api } from "@ui/assets/api";
import { initWorkspace } from "@ui/modules/workspace/events/index";
import { initStudy } from "@ui/modules/study/events/index";
import "@ui/assets/variables.css";
import "@ui/modules/auth/login/styles/index.css";
import "@ui/modules/workspace/styles/index.css";
import "@ui/modules/study/styles/index.css";
import "@ui/modules/discussion/styles/index.css";
import workspaceLayout from "@ui/modules/workspace/layout/index.html?raw";
import studyLayout from "@ui/modules/study/layout/index.html?raw";
import discussionLayout from "@ui/modules/discussion/layout/index.html?raw";

const TOKEN_KEY = "catachess_token";
const USER_ID_KEY = "catachess_user_id";

function readStored(key: string) {
  return localStorage.getItem(key) || sessionStorage.getItem(key);
}

function decodeUserIdFromToken(token: string | null) {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) base64 += "=";
    const payload = JSON.parse(atob(base64));
    return typeof payload.sub === "string" ? payload.sub : null;
  } catch {
    return null;
  }
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
  if (!token) return false;
  const userId = readStored(USER_ID_KEY) || ensureUserId(token);
  return Boolean(token && userId);
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
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await api.request("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (response?.access_token) {
        localStorage.setItem(TOKEN_KEY, response.access_token);
        const userId = decodeUserIdFromToken(response.access_token);
        if (userId) {
          localStorage.setItem(USER_ID_KEY, userId);
        }
        navigate(redirect, { replace: true });
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
            Don&apos;t have an account? <a href="#">Sign up</a>
          </p>
        </div>
      </div>
    </div>
  );
}

function WorkspaceSelect() {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";
    initWorkspace(containerRef.current, {
      onOpenStudy: (studyId) => navigate(`/workspace/${studyId}`),
    });
  }, [navigate]);

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
    containerRef.current.innerHTML = "";
    initStudy(containerRef.current, id);
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/workspace-select" replace />} />
        <Route path="/login" element={<LoginPage />} />
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
              <WorkspacePage />
            </Protected>
          }
        />
        <Route path="/workspace" element={<Navigate to="/workspace-select" replace />} />
        <Route path="*" element={<div>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}
