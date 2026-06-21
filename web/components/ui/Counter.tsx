"use client";

import { animate, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";

/** Counts a number up when scrolled into view. Renders via a format function. */
export function Counter({
  to,
  duration = 1.4,
  format,
  className = "",
}: {
  to: number;
  duration?: number;
  format: (v: number) => string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const controls = animate(0, to, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setVal(v),
    });
    return () => controls.stop();
  }, [inView, to, duration]);

  return (
    <span ref={ref} className={className}>
      {format(inView ? val : 0)}
    </span>
  );
}
