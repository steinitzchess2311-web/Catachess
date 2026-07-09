# Jul 8 Todo Execution Grill
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## topic Jul 8 todo execution

1. Should every item in `patch/docs/Jul_8_代办.md` be implemented in one code drop?
   Recommended answer: No. The list mixes low-risk UI polish with infrastructure, workers, permissions, realtime editing, and performance work. Use small production-safe loops so each completed item can be verified and deployed.

2. When should a todo line be marked `-[✅]`?
   Recommended answer: Only after the requirement is implemented, tested, committed, and production deployment is either complete or explicitly not required for that item.

3. Should engine worker and predictor infrastructure be marked done after a frontend mock?
   Recommended answer: No. Those items require server-side capacity controls, queues, and real connection paths before completion.

4. Should database permission changes be bundled with UI cleanup?
   Recommended answer: No. Study viewer/modifier separation changes persistence contracts and must ship behind migrations and compatibility checks.

5. What is the safest first loop?
   Recommended answer: Start with isolated profile cleanup items because the backend already stores online time and the frontend profile module is bounded.
