# Study breadcrumb overflow grill
Created at: 2026-07-08 21:21 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:21 EDT
Last Modified by: Codex

## topic Study breadcrumb overflow

1. Should study page breadcrumbs use horizontal scrolling?
   Recommended answer: No. Use the same compressed breadcrumb model as workspace so the header remains stable.

2. Which breadcrumb items should remain visible?
   Recommended answer: Always keep the first item and the last two items. Hide the middle ancestors behind `...` when the path is long.

3. How should hidden ancestors be accessed?
   Recommended answer: The `...` control opens a menu listing hidden ancestors. Selecting one follows the same unsaved-change navigation guard as a visible breadcrumb click.

4. Should study breadcrumb resolution keep a fixed maximum depth?
   Recommended answer: No. Use cycle detection instead of a depth cap so legitimate deep folder nesting can render safely.

5. Should current study breadcrumb be clickable?
   Recommended answer: No. Keep the current study as a non-clickable label; visible ancestors and hidden menu ancestors remain navigable.
