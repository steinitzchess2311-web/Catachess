## header
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Frontend engine analysis client, browser cache, Stockfish WASM wrapper, and precompute system.
- 架构思路: Auto mode prefers browser Stockfish WASM for responsive feedback; explicit Stockfish/AlphaZero modes call the backend engine API so server worker limits apply.

## folder structure
|-README.md intro to this folder
|-client.ts engine API client, engine mode routing, cache writes, and WASM fallback
|-types.ts shared engine result and engine mode types
|-parsers.ts Stockfish/WASM parser helpers
|-cache/ browser cache adapters and manager
|-precompute/ background precompute queue and storage
|-wasm/ Stockfish WASM loader and analysis runner

## 代办
- Add a frontend unit test for explicit engine mode request payloads.
