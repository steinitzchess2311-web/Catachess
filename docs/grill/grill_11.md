# Global Header Size Tuning Grill
Created at: 2026-07-08 18:43:55 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:43:55 EDT
Last Modified by: Codex

## topic global header size tuning

## questions
- Is the visible desktop header currently 100px?
  - No. The earlier CSS has `height: 100px`, but the later product refresh overrides it to 76px with a 70px logo.
- How much should "slightly taller" mean?
  - Increase the final desktop header from 76px to 84px and scale the logo/nav/action controls proportionally. This is visible but does not turn the header into a banner.
- Should the mobile header also grow?
  - No. Mobile already has tighter vertical constraints. Keep the mobile override compact so page content is not pushed down.
- Should this change alter navigation behavior?
  - No. This is a sizing pass only.
