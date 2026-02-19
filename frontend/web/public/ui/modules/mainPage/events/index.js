const routes = {
  login: '/login?redirect=/workspace/private',
  signup: '/signup?redirect=/workspace/private',
  account: '/account',
};

const TOKEN_KEY = 'catachess_token';
const USER_ID_KEY = 'catachess_user_id';

const readStored = (key) =>
  window.localStorage.getItem(key) || window.sessionStorage.getItem(key);

const decodeTokenPayload = (token) => {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length < 2) return null;
  try {
    let base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) base64 += '=';
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
};

const isTokenValid = (token) => {
  if (!token) return false;
  const payload = decodeTokenPayload(token);
  if (!payload) return false;
  if (typeof payload.exp !== 'number') return true;
  return payload.exp * 1000 > Date.now();
};

const ensureUserId = (token) => {
  const existing = readStored(USER_ID_KEY);
  if (existing) return existing;
  const payload = decodeTokenPayload(token);
  if (payload && typeof payload.sub === 'string') {
    window.localStorage.setItem(USER_ID_KEY, payload.sub);
    return payload.sub;
  }
  return null;
};

const applyHeaderState = () => {
  const token = readStored(TOKEN_KEY);
  const usernameLink = document.getElementById('header-username');
  const loginBtn = document.getElementById('top-login');
  const signupBtn = document.getElementById('top-signup');

  if (!isTokenValid(token)) {
    if (usernameLink) usernameLink.hidden = true;
    if (loginBtn) loginBtn.hidden = false;
    if (signupBtn) signupBtn.hidden = false;
    return;
  }

  const userId = readStored(USER_ID_KEY) || ensureUserId(token);
  if (usernameLink) {
    usernameLink.textContent = userId || 'Account';
    usernameLink.hidden = false;
  }
  if (loginBtn) loginBtn.hidden = true;
  if (signupBtn) signupBtn.hidden = true;
};

const bind = (id, target) => {
  const button = document.getElementById(id);
  if (!button) return;
  button.addEventListener('click', () => {
    window.location.assign(target);
  });
};

bind('top-login', routes.login);
bind('top-signup', routes.signup);
bind('main-login', routes.login);
bind('main-signup', routes.signup);
applyHeaderState();
