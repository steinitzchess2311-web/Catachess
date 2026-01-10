# Skeleton Layout Reference

Pure HTML/CSS layout skeleton with no functionality. All positioning uses percentage coordinates relative to `#app-frame`.

## Element IDs

All IDs match the renderer expectations:

**Header:**
- `#app-frame` - Main container (100% x 100%)
- `#header` - Header region
- `#left-long-bar`, `#button-b1` ~ `#button-b4`, `#search-box`, `#right-small-box`

**Left Column:**
- `#game-meta` - Game metadata
- `#player-info` - Player information
- `#chat-title-bar` - Chat header
- `#chat-messages` - Chat message area
- `#chat-input-area` - Chat input

**Center:**
- `#chess-board` - Chess board container

**Right Column:**
- `#clock-white`, `#clock-black` - Chess clocks
- `#move-history-list` - Move history
- `#action-resign`, `#action-draw`, `#action-takeback`, `#action-extra` - Action buttons

**Bottom:**
- `#bottom-long-bar` - Record bar

## Usage

Open `skeleton.html` directly in a browser to see the layout structure.

```bash
python3 -m http.server 7999
# Open: http://localhost:7999/skeleton.html
```
