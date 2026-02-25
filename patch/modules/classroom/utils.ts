// ─── Shared utilities ─────────────────────────────────────────────────────────

/**
 * Returns a human-readable due date string.
 * "Today", "Tomorrow", "Mar 5", etc.
 */
export function formatDue(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    const ago = Math.abs(diffDays);
    return ago === 1 ? 'yesterday' : `${ago} days ago`;
  }
  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'tomorrow';
  if (diffDays <= 6) return `in ${diffDays} days`;

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/**
 * Returns the CSS modifier class suffix for a due date.
 * Maps to .cl-asgn-card__due--{modifier}
 */
export function dueCssModifier(dateStr: string): 'overdue' | 'soon' | 'normal' {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffMs < 0) return 'overdue';
  if (diffHours <= 48) return 'soon';
  return 'normal';
}

/**
 * Returns urgency label for a due date.
 */
export function getUrgency(dateStr: string | null): 'overdue' | 'due_soon' | 'normal' {
  if (!dateStr) return 'normal';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffMs < 0) return 'overdue';
  if (diffHours <= 48) return 'due_soon';
  return 'normal';
}
