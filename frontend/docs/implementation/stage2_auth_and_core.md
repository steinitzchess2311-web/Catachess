# Stage 2: Authentication & Core UI

> **Goal:** Enable user registration, login, and secure session management.
> **Dependencies:** Stage 1 (API Client, CSS Variables).

## 1. Login Module (`ui/modules/auth/login/`)
- [x] **Create `layout/index.html`**:
    - [x] Create a `<template id="login-template">`.
    - [x] Add Email/Password inputs and "Sign In" button using `variables.css` classes.
- [x] **Create `styles/login.css`**:
    - [x] Style the card using `--surface`, `--radius-md`, and `--shadow-1`.
- [x] **Create `events/index.ts`**:
    - [x] **Event**: Form submit -> Call `ApiClient.post('/auth/login', {username, password})`.
    - [x] **Success**: Store token in `localStorage`, redirect to `/workspace`.
    - [x] **Error**: Show toast/alert using `--error` color.

## 2. Signup Module (`ui/modules/auth/signup/`)
- [x] **Create `layout/index.html`**:
    - [x] **Step 1 View**: Email input + "Create Account" button.
    - [x] **Step 2 View**: Verification Code input (6 chars) + "Verify" button + "Resend" link.
    - [x] Use `hidden` class to toggle steps.
- [x] **Create `events/index.ts`**:
    - [x] **Event (Step 1)**: Submit -> `ApiClient.post('/auth/register', {email})`. On success, show Step 2.
    - [x] **Event (Step 2)**: Input -> `ApiClient.post('/auth/verify-signup', {email, code})`. On success, redirect to Login.
    - [x] **Timer**: Implement 60s countdown for "Resend".

## 3. Router Integration (`index.html` shell)
- [x] **Update `index.html`**:
    - [x] Add a basic client-side router (hash-based or history API).
    - [x] **Routes**:
        - `/login` -> Load Login Module.
        - `/signup` -> Load Signup Module.
        - `/` -> Redirect to Login if no token, else Workspace.

## 4. Verification
- [x] **Flow Test**:
    1.  Open `/signup`.
    2.  Enter email. Check backend logs for "sent" code.
    3.  Enter code. Verify redirect to login.
    4.  Login. Verify token is in LocalStorage.