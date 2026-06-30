"use client";
import { useEffect, useRef } from "react";
import styles from "./MarketingBg.module.css";

const BAR_COUNT = 70;

/**
 * Animated front-door background: a full-bleed waveform of ~70 vertical bars
 * plus a radial glow. Ports the inline mockup script into a useEffect/setInterval.
 */
export function MarketingBg() {
  const waveRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = waveRef.current;
    if (!el) return;
    const bars = Array.from(el.children) as HTMLElement[];
    let t = 0;
    const id = setInterval(() => {
      t += 0.18;
      bars.forEach((b, i) => {
        const h = 20 + Math.abs(Math.sin(t + i * 0.35)) * 60 * (0.3 + Math.random() * 0.7);
        b.style.height = h.toFixed(0) + "%";
      });
    }, 110);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <div className={styles.glow} aria-hidden />
      <div className={styles.bgwave} ref={waveRef} aria-hidden>
        {Array.from({ length: BAR_COUNT }).map((_, i) => (
          <i key={i} />
        ))}
      </div>
    </>
  );
}
