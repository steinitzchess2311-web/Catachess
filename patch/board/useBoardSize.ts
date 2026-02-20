import { useEffect, useRef, useState } from 'react';

/**
 * Measures the width of a container element via ResizeObserver.
 * Returns a [ref, size] pair. The ref should be attached to the wrapper div;
 * `size` updates whenever the element's content box changes.
 *
 * Falls back to 500 until the first measurement arrives.
 */
export function useBoardSize(fallback = 500): [React.RefObject<HTMLDivElement>, number] {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(fallback);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Sync initial measurement before first paint
    const initial = el.getBoundingClientRect().width;
    if (initial > 0) setSize(Math.floor(initial));

    const obs = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w && w > 0) setSize(Math.floor(w));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return [containerRef, size];
}
