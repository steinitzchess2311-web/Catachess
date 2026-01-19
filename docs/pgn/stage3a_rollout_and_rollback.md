# Stage 3A: PGN V2 (ShowDTO) Rollout and Rollback Plan

**Owner:** @Catadragon
**Status:** In Progress (Grayscale Rollout)
**Date:** 2026-01-18

---

## 1. Summary

This document outlines the rollout and rollback strategy for the PGN V2 rendering engine (internally known as `ShowDTO`). The goal is to ensure a safe, staged release while maintaining the ability to immediately revert to the legacy system if issues arise.

## 2. Current Rollout Strategy: Grayscale

The PGN V2 feature is currently in a **grayscale rollout**.

-   **Default Status:** **DISABLED**
    -   The feature flag `USE_SHOW_DTO` defaults to `false` in the frontend code.
    -   See: `frontend/ui/modules/study/api/pgn.ts`

-   **Activation Mechanism:** **Whitelist via Local Storage**
    -   The feature is only active for users who are on the official whitelist and have the feature flag enabled in their browser's local storage.
    -   The auditable list of whitelisted users is maintained in `docs/pgn/rollout_whitelist.md`.

## 3. Rollback Plan

The rollback mechanism is designed for immediate, client-side execution.

### Immediate Rollback (Per-user or Global)

To revert to the legacy PGN rendering engine, set the `catachess_use_show_dto` flag in local storage to `false`.

**Execution:**

1.  Open the browser's developer console.
2.  Execute the following command:
    ```javascript
    localStorage.setItem('catachess_use_show_dto', 'false');
    window.location.reload();
    ```
3.  The application will now use the legacy rendering engine.

This procedure can be communicated to any user experiencing issues to allow for self-service rollback.

## 4. Transition to Full Rollout

The feature will be moved from grayscale to full rollout after the following conditions are met:

-   [ ] No critical bugs have been reported by whitelisted users for at least one week.
-   [ ] Performance metrics for the `/show` API endpoint are stable and within acceptable limits.
-   [ ] The manual acceptance checklist in `pgn/implementaion/stage2d.md` is fully completed and verified.

Once these conditions are met, the default value of `USE_SHOW_DTO` in `frontend/ui/modules/study/api/pgn.ts` will be changed to `true`.