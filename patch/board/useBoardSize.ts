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

    const measure = () => {
      const { width, height } = el.getBoundingClientRect();
      const s = Math.floor(Math.min(width || fallback, height || fallback));
      if (s > 0) setSize(s);
    };

    measure();
    const obs = new ResizeObserver(measure);
    obs.observe(el);
    return () => obs.disconnect();
  }, [fallback]);

  return [containerRef, size];
}
