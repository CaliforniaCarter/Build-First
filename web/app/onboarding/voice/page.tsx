"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingTop } from "@/components/OnboardingTop";
import { api, ApiError } from "@/lib/api";
import { Intake, completion } from "@/lib/intake";
import styles from "./page.module.css";

// Exact question text — these are the keys stored into voice.answers.
const PROMPTS = [
  {
    key: "weekend",
    q: "what'd you do last weekend?",
    placeholder: "dictate with your own Wispr Flow or type — like you'd text a friend",
    hint: "dictate with your own Wispr Flow — or just type",
    slot: "your rhythm",
  },
  {
    key: "lunch",
    q: "your go-to lunch — and why?",
    placeholder: "dictate with your own Wispr Flow or type…",
    hint: "however you'd say it is the point",
    slot: "sentence shape",
  },
  {
    key: "teach",
    q: "teach me something you're into — like i'm a friend.",
    placeholder: "dictate with your own Wispr Flow or type…",
    hint: "the more you, the better",
    slot: "words & tics",
  },
] as const;

// single-select tap groups (match the mockup's copy)
const HUMORS = ["dry & deadpan", "playful", "sharp / spicy", "mostly straight"];
const SHAPES = ["short & punchy", "a little story", "one big idea"];

function truncate(s: string, n = 90): string {
  const t = (s ?? "").trim();
  return t.length > n ? t.slice(0, n).trimEnd() + "…" : t;
}

export default function VoicePage() {
  const router = useRouter();
  const [intake, setIntake] = useState<Intake | null>(null);
  const [loadErr, setLoadErr] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [showErr, setShowErr] = useState(false);
  const [shake, setShake] = useState(false);
  const [focused, setFocused] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getIntake()
      .then((i) => alive && setIntake(i))
      .catch((e) => alive && setLoadErr(e));
    return () => {
      alive = false;
    };
  }, []);

  // ── editable local copy: every edit clones the intake immutably ──────────
  function setAnswer(q: string, val: string) {
    setIntake((p) =>
      p
        ? { ...p, voice: { ...p.voice, answers: { ...p.voice.answers, [q]: val } } }
        : p
    );
    setShowErr(false);
  }
  function pickHumor(label: string) {
    setIntake((p) => (p ? { ...p, voice: { ...p.voice, tone_words: [label] } } : p));
    setShowErr(false);
  }
  function pickShape(label: string) {
    setIntake((p) =>
      p
        ? {
            ...p,
            voice: { ...p.voice, sentence_length: label },
            output: { ...p.output, format: label },
          }
        : p
    );
    setShowErr(false);
  }

  // ── gentle loading / error states ────────────────────────────────────────
  if (loadErr) {
    const is409 = loadErr instanceof ApiError && loadErr.status === 409;
    return (
      <>
        <OnboardingTop active="voice" pct={0} />
        <main className="flex-1 flex items-center justify-center py-20">
          <div className="wrap text-center">
            <h1 className="serif text-[clamp(28px,4vw,42px)] mb-3">
              {is409 ? "let's finish the basics first" : "couldn't load your voice"}
            </h1>
            <p className="text-[15px] mb-6" style={{ color: "var(--muted)" }}>
              {is409
                ? "we need a couple earlier steps before tuning your voice."
                : "something went wrong reaching timbre — try again in a moment."}
            </p>
            <button className="cta" type="button" onClick={() => router.push("/onboarding/why")}>
              start from the why <span className="arrow">→</span>
            </button>
          </div>
        </main>
      </>
    );
  }

  if (!intake) {
    return (
      <>
        <OnboardingTop active="voice" pct={0} />
        <main className="flex-1 flex items-center justify-center py-20">
          <p className="text-[14px]" style={{ color: "var(--muted)" }}>
            tuning…
          </p>
        </main>
      </>
    );
  }

  // ── derived, all from the user's own inputs ─────────────────────────────
  const answers = intake.voice.answers;
  const pickedHumor = intake.voice.tone_words[0] ?? "";
  const pickedShape = intake.voice.sentence_length;

  const filledPrompts = PROMPTS.filter((p) => (answers[p.q] ?? "").trim().length > 0).length;
  const filledTaps = (pickedHumor ? 1 : 0) + (pickedShape ? 1 : 0);
  const filled = filledPrompts + filledTaps; // out of 5
  const formedPct = Math.round((filled / 5) * 100);

  // honest top meter — real intake completion
  const pct = completion(intake) * 100;

  // persona panel slots — echo ONLY what the user gave us
  const slots: { label: string; filled: boolean; value: string; chip: boolean }[] = [
    ...PROMPTS.map((p) => ({
      label: p.slot,
      filled: (answers[p.q] ?? "").trim().length > 0,
      value: truncate(answers[p.q] ?? ""),
      chip: false,
    })),
    { label: "humor", filled: !!pickedHumor, value: pickedHumor, chip: true },
    { label: "shape", filled: !!pickedShape, value: pickedShape, chip: true },
  ];

  async function go() {
    if (busy || !intake) return;
    if (filled === 0) {
      setShowErr(true);
      setShake(true);
      return;
    }
    setBusy(true);
    try {
      await api.patchIntake({ voice: intake.voice, output: intake.output });
      router.push("/onboarding/reveal");
    } catch {
      setBusy(false);
    }
  }

  return (
    <>
      <OnboardingTop active="voice" pct={pct} />
      <main className="flex-1 py-10">
        <div className="wrap">
          <h1 className="serif text-[clamp(34px,4vw,50px)]">
            now — how you <span className="hl">sound</span>.
          </h1>
          <p className="mt-3 text-[16px] max-w-[46ch]" style={{ color: "#C6C6C0" }}>
            answer a few easy things — write them like you&apos;d text a friend. dictate with your
            own Wispr Flow into any field, or just type.
          </p>

          <div className={styles.layout}>
            {/* LEFT: capture */}
            <section>
              {PROMPTS.map((p, i) => {
                const val = answers[p.q] ?? "";
                const answered = val.trim().length > 0;
                const isFocus = focused === p.key;
                return (
                  <div
                    key={p.key}
                    className={`${styles.prompt} ${isFocus ? styles.focus : ""} ${
                      answered ? styles.answered : ""
                    }`}
                  >
                    <div className={styles.q}>
                      <span className={styles.qn}>{i + 1}</span>
                      <span className={styles.qt}>{p.q}</span>
                    </div>
                    <textarea
                      className={styles.ta}
                      rows={2}
                      placeholder={p.placeholder}
                      value={val}
                      onChange={(e) => setAnswer(p.q, e.target.value)}
                      onFocus={() => setFocused(p.key)}
                      onBlur={() => setFocused((f) => (f === p.key ? null : f))}
                    />
                    <div className={styles.listen}>
                      <span className={styles.lw} aria-hidden>
                        {Array.from({ length: 10 }).map((_, j) => (
                          <i key={j} />
                        ))}
                      </span>
                      <span>{p.hint}</span>
                    </div>
                  </div>
                );
              })}

              <div className={styles.cardsec}>
                <h3>two quick taps — your humor</h3>
                <div className={styles.taps}>
                  {HUMORS.map((h) => (
                    <button
                      key={h}
                      type="button"
                      className={`chip ${pickedHumor === h ? "on" : ""}`}
                      onClick={() => pickHumor(h)}
                    >
                      {h}
                    </button>
                  ))}
                </div>
                <h3>…and your shape</h3>
                <div className={styles.taps}>
                  {SHAPES.map((s) => (
                    <button
                      key={s}
                      type="button"
                      className={`chip ${pickedShape === s ? "on" : ""}`}
                      onClick={() => pickShape(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.back}
                  onClick={() => router.push("/onboarding/profile")}
                >
                  ← back
                </button>
                <div className={styles.actr}>
                  <span
                    className={`err ${showErr ? "show" : ""}`}
                    style={{ display: "inline-block", marginTop: 0 }}
                  >
                    answer at least one — timbre needs something to hear.
                  </span>
                  <button
                    type="button"
                    className={`cta ${shake ? "shake" : ""}`}
                    onClick={go}
                    onAnimationEnd={() => setShake(false)}
                  >
                    {busy ? "tuning…" : "see my voice"} <span className="arrow">→</span>
                  </button>
                </div>
              </div>
            </section>

            {/* RIGHT: your voice, forming — reflects the user's own inputs only */}
            <aside className={styles.pp}>
              <div className={styles.ppHead}>
                <span className={styles.ppTitle}>your voice, forming</span>
              </div>
              <div className={styles.ppSub}>
                timbre turns these into your persona on the next screen — you&apos;ll confirm it.
              </div>
              <div className={styles.ppFile}>
                <span className={styles.liveWave} aria-hidden>
                  {Array.from({ length: 16 }).map((_, j) => (
                    <i key={j} />
                  ))}
                </span>
                persona.md
              </div>

              {slots.map((s) => (
                <div
                  key={s.label}
                  className={`${styles.pslot} ${s.filled ? styles.filled : ""}`}
                >
                  <div className={styles.plabel}>{s.label}</div>
                  {s.filled ? (
                    s.chip ? (
                      <div className={styles.pval}>
                        <span className={styles.chips}>
                          <span className={styles.vchip}>{s.value}</span>
                        </span>
                      </div>
                    ) : (
                      <div className={styles.pval}>{s.value}</div>
                    )
                  ) : (
                    <div className={styles.skel}>
                      <span />
                      <span />
                    </div>
                  )}
                </div>
              ))}

              <div className={styles.ppFoot}>
                <span>voice formed</span>
                <b>{formedPct}%</b>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </>
  );
}
