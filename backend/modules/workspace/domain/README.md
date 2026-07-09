## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Hold workspace domain models, services, policies, and business rules.
- 架构思路: Domain code owns permissions and workflows so endpoints can stay small and consistent.

## folder structure
|-models/ dataclasses and enum protocols.
|-policies/ permission and limit decisions.
|-services/ orchestration for node, study, sharing, search, and import behavior.

## 代办
- Continue moving cross-endpoint authorization logic into policies.
