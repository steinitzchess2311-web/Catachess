/**
 * Multi-PGN Splitter
 *
 * Splits a string that may contain multiple PGN games into individual game
 * strings.  Games are separated by a blank line followed by a new header block
 * (i.e. a line starting with '[').
 *
 * Matches Lichess MultiPgn.split behaviour.
 */

/** Delimiter: two newlines followed by a '[' (start of the next PGN header) */
const SPLIT_PATTERN = /\n\n(?=\[)/;

/**
 * Split a multi-game PGN string into individual game strings.
 *
 * @param content  Raw PGN text (may contain many games)
 * @param max      Maximum number of games to return (default 64)
 * @returns        Array of individual PGN strings (at most `max` elements)
 */
export function splitMultiPgn(content: string, max = 64): string[] {
  return content
    .replace(/\r/g, '')       // normalise line endings
    .split(SPLIT_PATTERN)
    .filter((s) => s.trim().length > 0)
    .slice(0, max);
}
