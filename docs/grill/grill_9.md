## topic workspace header product redesign

### 1. Is the visible path input necessary when the page already has breadcrumbs and a folder tree?

Recommended answer: no. The path input exposes an implementation model instead of a user task. It duplicates the breadcrumb and creates a second navigation concept.

Decision: remove the visible path jump from the main header. Keep breadcrumb navigation as the single visible current-location affordance.

### 2. What controls are essential in the workspace header?

Recommended answer: current location, create folder, create study, and sort. Search and workspace mode switching already live in the sidebar and should stay there.

Decision: redesign the header into a compact title/location block plus a right-aligned action bar.

### 3. Should sorting keep the current icon-only treatment?

Recommended answer: mostly yes, but the control needs clearer grouping and less visual weight. It should read as a secondary view option, not compete with create actions.

Decision: keep the date/clock icons and direction indicators, wrap them in a quiet segmented control, and remove the large uppercase "SORT" block from the page layout.

### 4. Should create actions remain as grid cards?

Recommended answer: keep the cards as useful empty-grid affordances, but add explicit header actions so the primary task is always visible when the grid scrolls or has many items.

Decision: add Create folder and Create study buttons in the header for private workspace mode only.

### 5. How should non-private modes differ?

Recommended answer: public, shared, and recycle views should not show creation actions. They should keep the same header skeleton so the page does not jump between modes.

Decision: render the action group, but hide create buttons outside private mode.
