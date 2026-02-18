/**
 * PGN Comment Parser
 *
 * Parses special Lichess-compatible annotations embedded inside PGN comment
 * braces { ... }:
 *
 *   [%csl Ge4,Rb2,Yc3]   → colored circles
 *   [%cal Ge2e4,Rc7c8]   → colored arrows
 *   [%clk H:MM:SS]        → clock remaining time (centiseconds)
 *   [%emt H:MM:SS]        → elapsed move time (centiseconds)
 *
 * Color prefix mapping: G=green  R=red  B=blue  Y=yellow
 */

import type { Shape, ShapeCircle, ShapeArrow, ShapeColor } from '../tree/type';

export interface ParsedComment {
  /** Board shapes (circles + arrows) */
  shapes: Shape[];
  /** Clock remaining time in centiseconds (from [%clk]) */
  clock: number | null;
  /** Elapsed move time in centiseconds (from [%emt]) */
  emt: number | null;
  /** Remaining plain-text after stripping all [%...] tags */
  text: string;
}

// ---------------------------------------------------------------------------
// Color prefix helpers
// ---------------------------------------------------------------------------

const COLOR_MAP: Record<string, ShapeColor> = {
  G: 'green',
  R: 'red',
  B: 'blue',
  Y: 'yellow',
};

function prefixToColor(prefix: string): ShapeColor {
  return COLOR_MAP[prefix.toUpperCase()] ?? 'green';
}

// ---------------------------------------------------------------------------
// Time string helper  H:MM:SS → centiseconds
// ---------------------------------------------------------------------------

function clkToCentiseconds(clk: string): number | null {
  const m = clk.trim().match(/^(\d+):(\d{1,2}):(\d{1,2})(?:\.\d+)?$/);
  if (!m) return null;
  const h = parseInt(m[1], 10);
  const min = parseInt(m[2], 10);
  const sec = parseInt(m[3], 10);
  return h * 360000 + min * 6000 + sec * 100;
}

// ---------------------------------------------------------------------------
// Main parser
// ---------------------------------------------------------------------------

/**
 * Parse the raw text of a PGN comment (content between { and }).
 */
export function parseComment(raw: string): ParsedComment {
  const shapes: Shape[] = [];
  let clock: number | null = null;
  let emt: number | null = null;

  // Replace each [%tag ...] annotation with empty string, collect results
  let text = raw.replace(/\[%(\w+)\s+([^\]]*)\]/g, (_match, tag: string, args: string) => {
    const tagUpper = tag.toUpperCase();

    if (tagUpper === 'CSL') {
      // Colored circles: Ge4,Rb2,...
      for (const part of args.split(',')) {
        const s = part.trim();
        if (s.length < 3) continue;
        const colorPrefix = s[0];
        const square = s.slice(1);
        if (/^[a-h][1-8]$/.test(square)) {
          shapes.push({ type: 'circle', color: prefixToColor(colorPrefix), square });
        }
      }
    } else if (tagUpper === 'CAL') {
      // Colored arrows: Ge2e4,Rc7c8,...
      for (const part of args.split(',')) {
        const s = part.trim();
        if (s.length < 5) continue;
        const colorPrefix = s[0];
        const from = s.slice(1, 3);
        const to = s.slice(3, 5);
        if (/^[a-h][1-8]$/.test(from) && /^[a-h][1-8]$/.test(to)) {
          shapes.push({ type: 'arrow', color: prefixToColor(colorPrefix), from, to });
        }
      }
    } else if (tagUpper === 'CLK') {
      clock = clkToCentiseconds(args);
    } else if (tagUpper === 'EMT') {
      emt = clkToCentiseconds(args);
    }

    return '';
  });

  // Clean up remaining whitespace
  text = text.replace(/\s+/g, ' ').trim();

  return { shapes, clock, emt, text };
}

// ---------------------------------------------------------------------------
// Serialization helpers (for PGN export round-trip)
// ---------------------------------------------------------------------------

const COLOR_PREFIX: Record<ShapeColor, string> = {
  green: 'G',
  red: 'R',
  blue: 'B',
  yellow: 'Y',
};

function centisToClkString(cs: number): string {
  const totalSec = Math.floor(cs / 100);
  const h = Math.floor(totalSec / 3600);
  const min = Math.floor((totalSec % 3600) / 60);
  const sec = totalSec % 60;
  return `${h}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

/** Serialize shapes and clock back into a PGN comment string (without the surrounding braces). */
export function serializeCommentParts(
  shapes: Shape[] | undefined,
  clock: number | null | undefined,
  text: string | null | undefined
): string {
  const parts: string[] = [];

  const circles = shapes?.filter((s): s is ShapeCircle => s.type === 'circle');
  if (circles && circles.length > 0) {
    parts.push(`[%csl ${circles.map((c) => `${COLOR_PREFIX[c.color]}${c.square}`).join(',')}]`);
  }

  const arrows = shapes?.filter((s): s is ShapeArrow => s.type === 'arrow');
  if (arrows && arrows.length > 0) {
    parts.push(`[%cal ${arrows.map((a) => `${COLOR_PREFIX[a.color]}${a.from}${a.to}`).join(',')}]`);
  }

  if (clock != null) {
    parts.push(`[%clk ${centisToClkString(clock)}]`);
  }

  if (text) parts.push(text);

  return parts.join(' ');
}
