## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Publish and classify workspace events used by activity, notifications, and collaboration refresh.
- 架构思路: Event types are stable taxonomy; `bus.py` writes event envelopes and helper functions create domain-specific payloads.

## folder structure
|-bus.py event publisher and helper publish functions.
|-types.py event enum and field constants.
|-payloads.py event envelope builder.
|-subscribers/ event subscriber registration.

## 代办
- Wire future websocket broadcasting from the same event stream.
