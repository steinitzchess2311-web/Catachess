# Stage 2: Authentication & Core UI

> **Goal:** Enable user registration, login, and secure session management.
> **Dependencies:** Stage 1 (API Client, CSS Variables).

## 1. Login Module (`ui/modules/auth/login/`)
- [ ] **Create `layout/index.html`**:
    - [ ] Create a `<template id="login-template">`.
    - [ ] Add Email/Password inputs and "Sign In" button using `variables.css` classes.
- [ ] **Create `styles/login.css`**:
    - [ ] Style the card using `--surface`, `--radius-md`, and `--shadow-1`.
- [ ] **Create `events/index.ts`**:
    - [ ] **Event**: Form submit -> Call `ApiClient.post('/auth/login', {username, password})`.
    - [ ] **Success**: Store token in `localStorage`, redirect to `/workspace`.
    - [ ] **Error**: Show toast/alert using `--error` color.

## 2. Signup Module (`ui/modules/auth/signup/`)
- [ ] **Create `layout/index.html`**:
    - [ ] **Step 1 View**: Email input + "Create Account" button.
    - [ ] **Step 2 View**: Verification Code input (6 chars) + "Verify" button + "Resend" link.
    - [ ] Use `hidden` class to toggle steps.
- [ ] **Create `events/index.ts`**:
    - [ ] **Event (Step 1)**: Submit -> `ApiClient.post('/auth/register', {email})`. On success, show Step 2.
    - [ ] **Event (Step 2)**: Input -> `ApiClient.post('/auth/verify-signup', {email, code})`. On success, redirect to Login.
    - [ ] **Timer**: Implement 60s countdown for "Resend".

## 3. Router Integration (`index.html` shell)
- [ ] **Update `index.html`**:
    - [ ] Add a basic client-side router (hash-based or history API).
    - [ ] **Routes**:
        - `/login` -> Load Login Module.
        - `/signup` -> Load Signup Module.
        - `/` -> Redirect to Login if no token, else Workspace.

## 4. Verification
- [ ] **Flow Test**:
    1.  Open `/signup`.
    2.  Enter email. Check backend logs for "sent" code.
    3.  Enter code. Verify redirect to login.
    4.  Login. Verify token is in LocalStorage.
