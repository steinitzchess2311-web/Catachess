# Stage 3: Workspace Module

> **Goal:** Display the file system (folders/studies) and enable navigation.
> **Dependencies:** Stage 2 (Auth).

## 1. Workspace Layout (`ui/modules/workspace/`)
- [ ] **Create `layout/index.html`**:
    - [ ] **Sidebar**: Navigation tree (Folders).
    - [ ] **Main Area**: Grid of items (Folders/Studies).
    - [ ] **Templates**: `<template id="folder-item">`, `<template id="study-item">`.
- [ ] **Create `styles/workspace.css`**:
    - [ ] Use Grid layout: `grid-template-columns: 250px 1fr`.
    - [ ] Sidebar background: `--surface` (or slightly darker).

## 2. Data Fetching (`events/index.ts`)
- [ ] **Fetch Nodes**:
    - [ ] On load: `ApiClient.get('/nodes?parent_id=root')`.
    - [ ] Render items using templates.
- [ ] **Navigation**:
    - [ ] Click Folder -> Update URL (pushState) -> Fetch new nodes.
    - [ ] Click Study -> Navigate to `/study/{id}`.

## 3. Creation Actions
- [ ] **New Folder/Study**:
    - [ ] Add "New" button (FAB or Header).
    - [ ] **Modal**: Use `ui/core/drag` to create a draggable "Create New" popup.
    - [ ] **Submit**: `ApiClient.post('/nodes', {type, name, parent_id})`.
    - [ ] **Refresh**: Re-fetch list on success.

## 4. Verification
- [ ] **Scenario**:
    1.  Login.
    2.  See "Root" folder (empty).
    3.  Create Folder "Openings".
    4.  Enter "Openings".
    5.  Create Study "Queen's Gambit".
    6.  Verify hierarchy persists on refresh.
