# Profile title header cleanup grill
Created at: 2026-07-08 21:07 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:07 EDT
Last Modified by: Codex

## topic Profile title header cleanup

1. Should ratings remain in the profile hero?
   Recommended answer: No. Ratings already live in the profile detail cards, so the hero should focus on identity and actions.

2. Should FIDE and Chinese titles render as separate badges?
   Recommended answer: No. The public identity should read as one line: `GM liquanhao` or `三运 liquanhao`.

3. What happens when both a FIDE title and a Chinese Chess Association title exist?
   Recommended answer: FIDE title wins in public display. Keep both editable, but show only the FIDE title in the hero prefix.

4. Should Chinese Chess Association titles stay as free text?
   Recommended answer: No. The form should expose fixed choices: `三运`, `二运`, `一运`, `候补`, `棋协`. This prevents noisy labels such as `国家三级运动员`.

5. How should old saved Chinese title values behave?
   Recommended answer: Normalize known legacy labels to the short option values on read/write, without a schema migration.

6. Should logout remain in the edit profile header?
   Recommended answer: No. Logout belongs on the profile page, while edit profile should stay focused on editing and saving.
