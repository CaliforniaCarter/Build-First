"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Brand } from "@/components/Brand";
import { api } from "@/lib/api";
import { getName, elapsedLabel } from "@/lib/onboarding-store";
import styles from "./page.module.css";

// Frozen 'signature' waveform — a fixed shape, not live audio.
const SIG_BARS = [
  14, 26, 40, 22, 52, 34, 18, 46, 30, 56, 24, 42, 16, 38, 50, 28, 44, 20, 34, 48, 22, 40, 30, 18,
];
const CONFETTI = [7, 19, 31, 43, 55, 67, 79, 88, 12, 24, 36, 48, 60, 72, 84, 5, 95, 15, 40, 65];
const COLORS = ["#FFE500", "#FFF18A", "#FAFAF7", "#FFC400"];

export default function DonePage() {
  const [name, setName] = useState("");
  const [elapsed, setElapsed] = useState("—");
  const [sig, setSig] = useState("");
  const [full, setFull] = useState(false);
  const [confettiOn, setConfettiOn] = useState(true);

  // name + REAL elapsed time live in localStorage — read after mount to stay hydration-safe
  useEffect(() => {
    setName(getName());
    setElapsed(elapsedLabel());
    const grow = setTimeout(() => setFull(true), 200);
    const clean = setTimeout(() => setConfettiOn(false), 6500);
    return () => {
      clearTimeout(grow);
      clearTimeout(clean);
    };
  }, []);

  // signature line: built from the real intake voice, falling back to persona.md
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const intake = await api.getIntake();
        const words = (intake.voice.tone_words ?? []).map((w) => w.trim()).filter(Boolean);
        const parts = [...words];
        const sl = intake.voice.sentence_length?.trim();
        if (sl) parts.push(sl);
        if (parts.length && !cancelled) {
          setSig(parts.join(" · "));
          return;
        }
      } catch {
        /* fall through to persona.md */
      }
      try {
        const docs = await api.getDocs();
        const first = docs.persona_md
          .split("\n")
          .map((l) => l.replace(/^#+\s*/, "").trim())
          .find(Boolean);
        if (first && !cancelled) setSig(first);
      } catch {
        /* leave the signature empty — the rest of the screen still stands */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const sigDisplay = sig ? `“${sig.replace(/[.\s]+$/, "")}.”` : "";

  return (
    <>
      <div className={styles.tprog}>
        <i className={full ? styles.full : ""} />
      </div>

      {confettiOn && (
        <div className={styles.confetti} aria-hidden>
          {CONFETTI.map((x, k) => (
            <i
              key={k}
              style={{
                left: `${x}%`,
                background: COLORS[k % COLORS.length],
                animationDuration: `${2.4 + (k % 5) * 0.4}s`,
                animationDelay: `${0.2 + (k % 6) * 0.12}s`,
                height: `${8 + (k % 4) * 3}px`,
              }}
            />
          ))}
        </div>
      )}

      <header className={styles.header}>
        <div className={`wrap ${styles.topbar}`}>
          <Brand />
          <div className={styles.crumbs}>
            <span className={styles.c}>✓</span> the why &nbsp;
            <span className={styles.c}>✓</span> you &nbsp;
            <span className={styles.c}>✓</span> your voice
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.stage}>
          <div className={styles.vp} aria-hidden>
            {SIG_BARS.map((h, k) => (
              <i key={k} style={{ height: `${h}px`, animationDelay: `${k * 0.05}s` }} />
            ))}
            <span className={styles.seal}>
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M4 12.5l5 5L20 6.5"
                  stroke="#0B0B0C"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          </div>

          <div className={styles.eyebrow}>
            voice captured · <span className={styles.t}>tuned in {elapsed}</span>
          </div>

          <h1 className={styles.headline}>
            you&apos;re <span className={styles.hl}>tuned</span>
            {name ? `, ${name.toLowerCase()}` : ""}.
          </h1>

          {sigDisplay && <div className={styles.sigline}>{sigDisplay}</div>}

          <p className={styles.lead}>
            drop in what you did — timbre writes the post, in your voice. every time.
          </p>

          <div className={styles.files}>
            <div className={styles.file}>
              <span className={styles.fi}>🗣️</span>
              <span>
                <span className={styles.ft}>
                  persona.md <span className={styles.chk}>✓</span>
                </span>
                <br />
                <span className={styles.fd}>how you sound</span>
              </span>
            </div>
            <div className={styles.file}>
              <span className={styles.fi}>🪪</span>
              <span>
                <span className={styles.ft}>
                  profile.md <span className={styles.chk}>✓</span>
                </span>
                <br />
                <span className={styles.fd}>who you are</span>
              </span>
            </div>
          </div>
          <div className={styles.saved}>
            🔒 saved on your machine — local-first, never uploaded.
          </div>

          <div className={styles.ctas}>
            <Link className="cta" href="/home">
              enter timbre <span className="arrow">→</span>
            </Link>
            <div className={styles.subnav}>
              <Link href="/compose">write your first post</Link>
              <Link href="/profile">your voice profile</Link>
              <Link href="/">↺ restart tour</Link>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
