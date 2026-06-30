"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingTop } from "@/components/OnboardingTop";
import { api, ApiError, type Insight } from "@/lib/api";
import { completion } from "@/lib/intake";
import styles from "./page.module.css";

type Phase = "loading" | "ready" | "blocked" | "error";
type Verdict = "yes" | "no";

// Render the persona.md fallback as light sections (only used when no insights come back).
function splitPersona(md: string): { title: string; body: string }[] {
  const out: { title: string; body: string }[] = [];
  let cur: { title: string; body: string } | null = null;
  for (const raw of md.split("\n")) {
    const h = raw.match(/^#{1,6}\s+(.*)$/);
    if (h) {
      if (cur) out.push(cur);
      cur = { title: h[1].trim(), body: "" };
    } else if (cur) {
      cur.body += (cur.body ? "\n" : "") + raw;
    } else if (raw.trim()) {
      cur = { title: "", body: raw };
    }
  }
  if (cur) out.push(cur);
  return out
    .map((s) => ({ title: s.title, body: s.body.trim() }))
    .filter((s) => s.title || s.body);
}

export default function RevealPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("loading");
  const [insights, setInsights] = useState<Insight[]>([]);
  const [sections, setSections] = useState<{ title: string; body: string }[]>([]);
  const [verdicts, setVerdicts] = useState<Record<number, Verdict>>({});
  const [pct, setPct] = useState(0);
  const [errMsg, setErrMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // honest "voice tuned" meter — non-critical, never blocks the reveal
      try {
        const intake = await api.getIntake();
        if (!cancelled) setPct(Math.round(completion(intake) * 100));
      } catch {
        /* leave the meter as-is */
      }
      try {
        await api.buildProfile(); // deterministic
        await api.buildPersona(); // LIVE — writes persona.md
        const { insights: found } = await api.personaInsights(); // LIVE — quote-grounded
        if (cancelled) return;
        if (found.length === 0) {
          // never leave the screen empty — fall back to the persona doc itself
          const docs = await api.getDocs();
          if (cancelled) return;
          setSections(splitPersona(docs.persona_md));
        } else {
          setInsights(found);
          const seed: Record<number, Verdict> = {};
          found.forEach((_, i) => (seed[i] = "yes"));
          setVerdicts(seed);
        }
        setPhase("ready");
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 409) {
          setPhase("blocked");
        } else {
          setErrMsg(e instanceof Error ? e.message : "something went sideways.");
          setPhase("error");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const traits = Array.from(
    new Set(insights.map((i) => i.trait_label.trim()).filter(Boolean))
  );

  return (
    <>
      <OnboardingTop active="voice" pct={pct} />
      <main className="flex-1 flex items-center py-12">
        <div className="wrap">
          <div className={styles.stage}>
            {phase === "loading" && (
              <div className={styles.composing}>
                <div className={styles.cw} aria-hidden>
                  {Array.from({ length: 26 }).map((_, i) => (
                    <i key={i} style={{ animationDelay: `${(i % 13) * 0.07}s` }} />
                  ))}
                </div>
                <h2 className={styles.composingTitle}>listening back to you…</h2>
              </div>
            )}

            {phase === "blocked" && (
              <div className={styles.center}>
                <h1 className="serif text-[clamp(34px,5vw,52px)]">
                  let&apos;s finish <span className="hl">setting up.</span>
                </h1>
                <p className="mt-4 text-[16px]" style={{ color: "var(--muted)" }}>
                  we need a little more of your voice before the reveal.
                </p>
                <div className="mt-7">
                  <button
                    className="cta"
                    type="button"
                    onClick={() => router.push("/onboarding/why")}
                  >
                    pick up where we left off <span className="arrow">→</span>
                  </button>
                </div>
              </div>
            )}

            {phase === "error" && (
              <div className={styles.center}>
                <h1 className="serif text-[clamp(34px,5vw,52px)]">
                  that didn&apos;t <span className="hl">land.</span>
                </h1>
                <p className="mt-4 text-[15px]" style={{ color: "var(--muted)" }}>
                  {errMsg}
                </p>
                <div className="mt-7 flex items-center justify-center gap-3">
                  <button
                    className="cta"
                    type="button"
                    onClick={() => window.location.reload()}
                  >
                    try again <span className="arrow">→</span>
                  </button>
                  <button
                    className="btn-ghost"
                    type="button"
                    onClick={() => router.push("/onboarding/voice")}
                  >
                    back to your voice
                  </button>
                </div>
              </div>
            )}

            {phase === "ready" && (
              <>
                <h1
                  className={`serif text-[clamp(40px,6vw,68px)] ${styles.ani}`}
                  style={{ animationDelay: "0s" }}
                >
                  here&apos;s what <span className="hl">i heard.</span>
                </h1>
                <p
                  className={`${styles.lead} ${styles.ani}`}
                  style={{ animationDelay: ".08s" }}
                >
                  every line below comes straight from what you just said — your words, not
                  ours. tap anything that&apos;s off.
                </p>

                {insights.length > 0 ? (
                  <>
                    <div className={styles.insights}>
                      {insights.map((ins, i) => {
                        const muted = verdicts[i] === "no";
                        return (
                          <div
                            key={i}
                            className={styles.ani}
                            style={{ animationDelay: `${0.12 + i * 0.08}s` }}
                          >
                            <div
                              className={`${styles.insight} ${muted ? styles.muted : ""}`}
                            >
                              <div className={styles.obs}>{ins.observation}</div>
                              <div className={styles.yn}>
                                <button
                                  type="button"
                                  className={`${styles.yes} ${
                                    verdicts[i] === "yes" ? styles.on : ""
                                  }`}
                                  onClick={() =>
                                    setVerdicts((v) => ({ ...v, [i]: "yes" }))
                                  }
                                >
                                  sounds like me
                                </button>
                                <button
                                  type="button"
                                  className={`${styles.no} ${
                                    verdicts[i] === "no" ? styles.on : ""
                                  }`}
                                  onClick={() =>
                                    setVerdicts((v) => ({ ...v, [i]: "no" }))
                                  }
                                >
                                  not quite
                                </button>
                              </div>
                              {ins.verbatim_quote.trim() && (
                                <div className={styles.receipt}>
                                  <span className={styles.receiptLabel}>you said</span>
                                  <span className={styles.quote}>
                                    &ldquo;<b>{ins.verbatim_quote}</b>&rdquo;
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {traits.length > 0 && (
                      <div
                        className={`${styles.summary} ${styles.ani}`}
                        style={{ animationDelay: `${0.12 + insights.length * 0.08}s` }}
                      >
                        <div className={styles.summaryLabel}>so — this is your voice</div>
                        <div className={styles.chips}>
                          {traits.map((t) => (
                            <span key={t} className={styles.sumChip}>
                              {t}
                            </span>
                          ))}
                        </div>
                        <div className={styles.note}>
                          timbre writes like this — and never posts anything without you.
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className={styles.insights}>
                    {sections.map((s, i) => (
                      <div
                        key={i}
                        className={`${styles.personaCard} ${styles.ani}`}
                        style={{ animationDelay: `${0.12 + i * 0.06}s` }}
                      >
                        {s.title && <div className={styles.personaTitle}>{s.title}</div>}
                        {s.body && <div className={styles.personaBody}>{s.body}</div>}
                      </div>
                    ))}
                  </div>
                )}

                <div
                  className={`${styles.confirm} ${styles.ani}`}
                  style={{ animationDelay: `${0.2 + insights.length * 0.08}s` }}
                >
                  <button
                    className="cta"
                    type="button"
                    onClick={() => router.push("/onboarding/done")}
                  >
                    yep, that&apos;s me <span className="arrow">→</span>
                  </button>
                  <button
                    className="btn-ghost"
                    type="button"
                    onClick={() => router.push("/onboarding/voice")}
                  >
                    let me edit one
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
