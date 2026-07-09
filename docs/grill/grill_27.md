Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex

## topic classroom product redesign

### Q1. What is the user actually asking for?
The classroom pages should stop feeling like a decorative demo and align with the product language already used in workspace and study: blue/white, clear hierarchy, restrained cards, compact controls, and product-grade modals.

### Q2. What should remain unchanged?
Core classroom behavior must remain unchanged: list classrooms, create classroom, join classroom, open classroom detail, view assignments, view members, invite members, broadcast announcements, contact teacher, share workspace, archive/delete/leave/rename.

### Q3. What is the highest-risk design problem?
The current module mixes inline styles, decorative shadows, colored badges, native confirm/alert dialogs, and oversized modal treatment. A CSS-only pass would leave interaction surfaces inconsistent because many components override layout inline.

### Q4. What is the product direction?
Use a quiet operational interface: white surfaces, blue primary actions, slate text, 8px radii, border-led separation, compact cards, segmented tabs, restrained menus, and modal dialogs that behave like workspace/study tooling instead of marketing cards.

### Q5. What should be removed?
Remove the logo-led marketing header, decorative card accents, hover lift effects, colorful category badges where color does not encode urgent state, native browser confirms/alerts in the primary classroom shell, and visible helper copy that repeats what the control already says.

### Q6. What should be tested before marking complete?
Run the frontend build, inspect the classroom pages via screenshot where feasible, and verify no TypeScript/CSS regression breaks routing or modal rendering. Native browser dialogs should not remain for the main classroom shell actions.

### Q7. What should not block this loop?
The broader classroom feature backend, study permissions, blog, catachat account integration, and notification bugs are separate remaining Jul 8 tasks. They should not be mixed into this UI redesign commit.
