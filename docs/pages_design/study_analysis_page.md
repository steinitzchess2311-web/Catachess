# Study And Analysis Page Design

## header
Created at: 2026-07-08 20:33 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:20 EDT
Last Modified by: Codex

## Page Job
- Let a chess user analyze positions, save analysis into studies, manage study chapters, and review move trees without visual clutter.

## Layout
- Analysis page header owns the page title and the "Send to Study" action.
- Analysis board remains the central object; sidebars should read as utilitarian work panels.
- Study page header owns breadcrumb, title, save state, chapter actions, and train/share affordances.
- Study page breadcrumbs compress long paths: first item, `...` overflow menu, and last two items remain visible.
- Study breadcrumb hidden ancestors remain navigable through the `...` menu and must respect unsaved-change warnings.
- Right panels should prioritize move tree and explorer workflows with compact tabs and predictable scrolling.
- Analysis sidebars expose compact controls for Depth, Lines, Engine on/off, and Engine choice.
- Predictor sidebars expose provider, top-k, Elo, enable control, and probability rows for human-like move prediction.
- Engine choice options are Auto, Stockfish, and AlphaZero; unavailable engines must report plain errors instead of silently showing another engine's result.

## Modal Rules
- Study and analysis workflow modals use the `.patch-modal` family.
- Modal cards use white surface, slate text, 8-10px radius, restrained shadow, and blue primary buttons.
- Do not use decorative emoji in modal titles or action labels.
- Chapter creation keeps only the necessary modes: Empty, From FEN, From PGN.
- Large PGN import must explain the split/import outcome with progress and final counts, not decorative copy.
- "Send to Study" picker should look like a product picker: header, breadcrumb row, scrollable node list, and explicit footer action.

## Visual Direction
- Blue and white product language shared with workspace.
- Compact information density.
- No oversized hero treatment, colorful decorative blocks, or hidden hover-only explanations.
- Engine analysis panels use white surfaces, thin borders, small rank markers, and restrained score colors.
- Predictor panels use the same white/blue product language as engine panels, but labels must say Predictor/Probability rather than Engine/Eval.

## 代办
- Continue aligning train launcher and opening trainer modals in a later pass.
