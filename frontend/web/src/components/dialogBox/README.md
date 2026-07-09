# Dialog Box Components

## header
Created at: 2026-07-08 20:12 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: React dialog components used by workspace node actions and related workspace flows.
- 架构思路: Keep behavior inside each modal component, while shared modal chrome lives in `Dialog.css` with the `cc-dialog-` prefix to avoid leaking into unrelated modules.

## folder structure
|-Dialog.css shared workspace/study dialog primitives
|-CreateModal.tsx creates workspace folders and studies
|-CreateModal.css create modal compatibility styles
|-DeleteModal.tsx moves a workspace node to recycle
|-DeleteModal.css delete modal compatibility styles
|-DragMoveModal.tsx confirms drag-and-drop moves
|-DragMoveModal.css drag move compatibility styles
|-FolderTree.tsx folder picker tree for move flows
|-FolderTreeItem.tsx expandable folder row
|-LogoutButton.tsx centered logout confirmation dialog with token clearing
|-LogoutButton.css logout confirmation dialog styles
|-MoveModal.tsx moves a workspace node to a destination folder
|-MoveModal.css move modal folder picker styles
|-NodeActionsModal.tsx action sheet for workspace nodes with title-only header and body metadata
|-NodeActionsModal.css action sheet compatibility styles
|-NodeShareModal.tsx icon-label visibility choices and user sharing dialog
|-NodeShareModal.css share dialog custom styles
|-RenameModal.tsx renames workspace nodes
|-RenameModal.css rename modal compatibility styles
|-TestSign.tsx legacy test sign component
|-TestSign.css legacy test sign styles
|-TrashActionsModal.tsx action sheet for recycled workspace nodes

## 代办
- Migrate older compatibility CSS files into `Dialog.css` once all callers use the shared class names exclusively.
