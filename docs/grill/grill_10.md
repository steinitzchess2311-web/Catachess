## topic explorer player color filters

### 1. Should year filters stay visible when player filters are active?

Recommended answer: no. The current UI says the filters are paused, which is extra cognitive load and exposes an implementation caveat.

Decision: hide the year filter card while at least one player is selected.

### 2. What is the default year lower bound when no player is selected?

Recommended answer: the UI should not imply that the database starts in 1995. The default lower bound must be the database's earliest known year.

Decision: change the visible default/min from 1995 to the current database minimum valid year. The current API returns an invalid `year: 31` anomaly before nineteenth-century games, so use the earliest valid game year, 1859.

### 3. How should player side filtering work?

Recommended answer: use a segmented control scoped to selected players: All, White, Black. The labels should describe the selected player's color, not the game's result.

Decision: add a player color filter with values `any`, `white`, and `black`. It is visible only when a player filter exists.

### 4. Should the side filter affect both move stats and game list?

Recommended answer: yes. If the user selects "White", both the move table and the game list must use only games where the selected player appears as White.

Decision: pass `player_color` to both `/masters` and `/masters/games`.
