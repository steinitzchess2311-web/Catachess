# PGN V2 (ShowDTO) Rollout Whitelist

**Owner:** @Catadragon
**Last Updated:** 2026-01-18

This document lists the users, teams, or other criteria that define the whitelist for the PGN V2 rendering engine (`USE_SHOW_DTO`). This feature is currently in a staged rollout and is **disabled by default**.

## How to Enable

For whitelisted users, the feature can be enabled via the browser's developer console by running:

```javascript
localStorage.setItem('catachess_use_show_dto', 'true');
window.location.reload();
```

To disable it, run:

```javascript
localStorage.setItem('catachess_use_show_dto', 'false');
window.location.reload();
```

---

## Whitelisted Users & Groups

This section serves as the auditable record of who has access to the feature during the grayscale rollout.

### Internal Teams

| Team / Group | Status | Date Added | Notes |
| :--- | :--- | :--- | :--- |
| **QA Team** | Active | 2026-01-15 | For testing and verification. |
| **Frontend Devs**| Active | 2026-01-15 | For development and debugging. |

### Beta Testers (User IDs)

| User ID | Username | Status | Date Added | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `user:101` | `test_user_alpha` | Active | 2026-01-18 | Initial beta tester. |
| `user:102` | `another_tester` | Pending | - | |

---

*This file must be updated before any changes to the whitelist are made.*