# Profile Online Time And Logout Polish Grill
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## topic Profile online time and logout polish

1. Should total online time be recalculated in the profile endpoint?
   Recommended answer: No. The database already stores `total_online_seconds`; profile endpoints should expose it without adding expensive work to public profile reads.

2. Should the public profile call the statistics endpoint separately?
   Recommended answer: No. Public profile is unauthenticated and should render from one profile response. Add the existing stored statistic to the profile response instead.

3. Should Chinese Chess Association wording keep the space?
   Recommended answer: No. Use `中国棋协称号` in the edit form label while keeping the English parenthetical for clarity.

4. How should title color be applied?
   Recommended answer: Render the title as its own inline span in the hero name and color only that prefix orange so the username remains the main identity.

5. Should logout remain a small popover?
   Recommended answer: No. Use a centered confirmation dialog with a dim backdrop, clear primary/cancel actions, Escape/outside dismissal, and no nested card styling.
