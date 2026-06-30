"use client";
import { useEffect, useRef } from "react";

export function Waveform({ bars = 22, className = "wave" }: { bars?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const items = Array.from(el.children) as HTMLElement[];
    let t = 0;
    const id = setInterval(() => {
      t += 0.35;
      items.forEach((b, i) => {
        const h = 6 + Math.abs(Math.sin(t + i * 0.5)) * 14 * (0.5 + Math.random() * 0.5);
        b.style.height = h.toFixed(1) + "px";
      });
    }, 90);
    return () => clearInterval(id);
  }, []);
  return (
    <span ref={ref} className={className} aria-hidden>
      {Array.from({ length: bars }).map((_, i) => (
        <i key={i} />
      ))}
    </span>
  );
}
