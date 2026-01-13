# Stage 3: Workspace Module

> **Goal:** Display the file system (folders/studies) and enable navigation.
> **Dependencies:** Stage 2 (Auth).

## 1. Workspace Layout (`ui/modules/workspace/`)
- [x] **Create `layout/index.html`**:
    - [x] **Sidebar**: Navigation tree (Folders).
    - [x] **Main Area**: Grid of items (Folders/Studies).
    - [x] **Templates**: `<template id="folder-item">`, `<template id="study-item">`.
- [x] **Create `styles/workspace.css`**: (Named `styles/index.css` per Protocol)
    - [x] Use Grid layout: `grid-template-columns: 250px 1fr`.
    - [x] Sidebar background: `--surface` (or slightly darker).

## 2. Data Fetching (`events/index.ts`)
- [x] **Fetch Nodes**:
    - [x] On load: `ApiClient.get('/nodes?parent_id=root')`.
    - [x] Render items using templates.
- [x] **Navigation**:
    - [x] Click Folder -> Update URL (pushState) -> Fetch new nodes.
    - [x] Click Study -> Navigate to `/study/{id}`.

## 3. Creation Actions
- [x] **New Folder/Study**:
    - [x] Add "New" button (FAB or Header).
    - [x] **Modal**: Use `ui/core/drag` to create a draggable "Create New" popup.
    - [x] **Submit**: `ApiClient.post('/nodes', {type, name, parent_id})`.
    - [x] **Refresh**: Re-fetch list on success.

## 4. Verification
- [x] **Scenario**:
    1.  Login.
    2.  See "Root" folder (empty).
    3.  Create Folder "Openings".
    4.  Enter "Openings".
    5.  Create Study "Queen's Gambit".
    6.  Verify hierarchy persists on refresh.