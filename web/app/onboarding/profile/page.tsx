"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { OnboardingTop } from "@/components/OnboardingTop";
import { api, ApiError } from "@/lib/api";
import { completion, type Intake, type Online, type Docs, type Typed } from "@/lib/intake";
import { getName } from "@/lib/onboarding-store";
import styles from "./page.module.css";

type SectionId = "online" | "resume" | "lines";
const ORDER: SectionId[] = ["online", "resume", "lines"];
type Status = "start" | "connected" | "optional" | "added" | "skipped";

const Check = () => (
  <svg viewBox="0 0 12 12" aria-hidden="true">
    <path
      d="M2 6.2l2.6 2.6L10 3"
      stroke="#0B0B0C"
      strokeWidth="2"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default function ProfilePage() {
  const router = useRouter();

  const [local, setLocal] = useState<Intake | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [loadErr, setLoadErr] = useState<{ msg: string; backToWhy: boolean } | null>(null);

  const [open, setOpen] = useState<SectionId | null>("online");
  const [addressed, setAddressed] = useState<Set<SectionId>>(new Set());
  const [status, setStatus] = useState<Record<SectionId, Status>>({
    online: "start",
    resume: "optional",
    lines: "optional",
  });

  const [scanState, setScanState] = useState<"idle" | "scanning" | "done">("idle");
  const [scanResult, setScanResult] = useState<{ count: number; pending: boolean } | null>(null);
  const lastScanKey = useRef<string>("");

  const [resumeErr, setResumeErr] = useState(false);
  const [resumeShake, setResumeShake] = useState(false);
  const [busy, setBusy] = useState(false);

  // ── load the intake once; keep an editable local copy ──────────────────────
  useEffect(() => {
    setDisplayName(getName().toLowerCase());
    (async () => {
      try {
        const intake = await api.getIntake();
        setLocal(intake);
        if (!getName() && intake.name) setDisplayName(intake.name.toLowerCase());
      } catch (e) {
        if (e instanceof ApiError && e.status === 409)
          setLoadErr({ msg: "let's finish the first step before this one.", backToWhy: true });
        else setLoadErr({ msg: "couldn't load your profile — refresh to try again.", backToWhy: false });
      }
    })();
  }, []);

  const pct = local ? completion(local) * 100 : 0;
  const who = (displayName || local?.name || "").trim().toLowerCase();

  // ── immutable nested setters ───────────────────────────────────────────────
  const setOnline = (p: Partial<Online>) =>
    setLocal((s) => (s ? { ...s, online: { ...s.online, ...p } } : s));
  const setDocs = (p: Partial<Docs>) =>
    setLocal((s) => (s ? { ...s, docs: { ...s.docs, ...p } } : s));
  const setTyped = (p: Partial<Typed>) =>
    setLocal((s) => (s ? { ...s, typed: { ...s.typed, ...p } } : s));

  function nextUnaddressed(after: SectionId, addr: Set<SectionId>): SectionId | null {
    const i = ORDER.indexOf(after);
    for (let j = i + 1; j < ORDER.length; j++) if (!addr.has(ORDER[j])) return ORDER[j];
    for (const id of ORDER) if (!addr.has(id)) return id;
    return null;
  }

  // ── honest post scan (LinkedIn / X) ────────────────────────────────────────
  async function runScan() {
    if (!local) return;
    const li = local.online.linkedin.trim();
    const x = local.online.x.trim();
    if (li.length <= 3 && x.length <= 3) return; // nothing meaningful to scan
    const key = `${li}|${x}`;
    if (scanState === "scanning") return;
    if (key === lastScanKey.current && scanState === "done") return;
    lastScanKey.current = key;
    setScanState("scanning");
    setScanResult(null);
    try {
      const res = await api.scan(li, x);
      const count = (res.linkedin?.post_count ?? 0) + (res.x?.post_count ?? 0);
      setScanResult({ count, pending: res.pending || count === 0 });
      // scan updated the intake server-side — merge the fresh online slice,
      // but keep the handles the user is typing right now.
      try {
        const fresh = await api.getIntake();
        setLocal((s) =>
          s ? { ...s, online: { ...fresh.online, linkedin: s.online.linkedin, x: s.online.x } } : s,
        );
      } catch {
        /* keep local copy */
      }
    } catch {
      setScanResult({ count: 0, pending: true });
    } finally {
      setScanState("done");
    }
  }

  // ── advance / skip a section (autosave the changed slice) ───────────────────
  async function advance(id: SectionId) {
    if (!local || busy) return;
    if (id === "resume" && !local.docs.resume.trim()) {
      setResumeErr(true);
      setResumeShake(true);
      return;
    }
    const addr = new Set(addressed).add(id);
    setAddressed(addr);
    setStatus((st) => ({ ...st, [id]: id === "online" ? "connected" : "added" }));
    try {
      if (id === "online") {
        await runScan();
        await api.patchIntake({ online: local.online });
      } else if (id === "resume") {
        await api.patchIntake({ docs: local.docs });
      } else {
        await api.patchIntake({ typed: local.typed });
      }
    } catch {
      /* autosave is best-effort; the continue CTA patches everything again */
    }
    setOpen(nextUnaddressed(id, addr));
  }

  function skip(id: SectionId) {
    if (busy) return;
    const addr = new Set(addressed).add(id);
    setAddressed(addr);
    setStatus((st) => ({ ...st, [id]: "skipped" }));
    setOpen(nextUnaddressed(id, addr));
  }

  async function onContinue() {
    if (!local || busy) return;
    setBusy(true);
    try {
      await api.patchIntake({ online: local.online, docs: local.docs, typed: local.typed });
      router.push("/onboarding/voice");
    } catch {
      setBusy(false);
    }
  }

  // ── right-rail checklist (real filled fields) ──────────────────────────────
  const checks = local
    ? [
        { label: "your name", sub: who || undefined, done: !!local.name.trim() },
        {
          label: "your links & posts",
          sub: "linkedin / x",
          done: !!(local.online.linkedin.trim() || local.online.x.trim()),
        },
        { label: "your role & lane", sub: undefined, done: !!local.typed.identity.trim() },
        { label: "what you're known for", sub: undefined, done: !!local.typed.known_for.trim() },
        { label: "a belief you'd defend", sub: undefined, done: !!local.typed.beliefs.trim() },
      ]
    : [];
  const doneCount = checks.filter((c) => c.done).length;
  const pcPct = checks.length ? Math.round((doneCount / checks.length) * 100) : 0;

  const iconActive = (id: SectionId) =>
    open === id || status[id] === "connected" || status[id] === "added";

  function StatusPill({ id }: { id: SectionId }) {
    const s = status[id];
    if (id === "online") {
      if (s === "connected") return <span className={styles.stDone}>connected</span>;
      if (s === "skipped") return <span className={styles.stSkip}>skipped</span>;
      return <span className={styles.startPill}>start here</span>;
    }
    if (s === "added") return <span className={styles.stDone}>added</span>;
    if (s === "skipped") return <span className={styles.stSkip}>skipped</span>;
    return <span className={styles.opt}>optional</span>;
  }

  return (
    <>
      <OnboardingTop active="you" pct={pct} />
      <main className="flex-1 py-10">
        {loadErr ? (
          <div className="wrap py-20 text-center">
            <p className="text-[16px]" style={{ color: "var(--muted)" }}>
              {loadErr.msg}
            </p>
            {loadErr.backToWhy && (
              <Link href="/onboarding/why" className="cta mt-6 inline-flex">
                start onboarding <span className="arrow">→</span>
              </Link>
            )}
          </div>
        ) : !local ? (
          <div className="wrap py-20" style={{ color: "var(--dim)" }}>
            loading…
          </div>
        ) : (
          <div className={`wrap ${styles.layout}`}>
            <section>
              <h1 className={`serif ${styles.h1}`}>the basics{who ? `, ${who}` : ""}.</h1>
              <p className={styles.sub}>
                the more timbre knows, the more it sounds like you. add what&apos;s easy — it&apos;ll
                nudge you for the rest. short on time? dictate any field with your own Wispr Flow.
              </p>

              <div className={styles.sources}>
                {/* 1 · ONLINE */}
                <div className={`${styles.src} ${open === "online" ? styles.srcOpen : ""}`}>
                  <button
                    className={styles.srcHead}
                    type="button"
                    onClick={() => setOpen((c) => (c === "online" ? null : "online"))}
                  >
                    <span
                      className={`${styles.srcIc} ${iconActive("online") ? styles.srcIcActive : ""}`}
                    >
                      🔗
                    </span>
                    <span className={styles.srcTt}>
                      <b>find me online</b>
                      <span>drop your links — timbre reads your profile &amp; posts</span>
                    </span>
                    <span className={styles.srcStatus}>
                      <StatusPill id="online" />
                    </span>
                    <span className={`${styles.caret} ${open === "online" ? styles.caretOpen : ""}`}>
                      ▾
                    </span>
                  </button>
                  <div
                    className={`${styles.srcBody} ${open === "online" ? styles.srcBodyOpen : ""}`}
                  >
                    <div className={styles.srcInner}>
                      <div className={styles.two}>
                        <div className={styles.row}>
                          <label className={styles.label}>LinkedIn</label>
                          <input
                            className={styles.input}
                            type="text"
                            placeholder="linkedin.com/in/you"
                            autoComplete="off"
                            value={local.online.linkedin}
                            onChange={(e) => setOnline({ linkedin: e.target.value })}
                            onBlur={runScan}
                          />
                        </div>
                        <div className={styles.row}>
                          <label className={styles.label}>X / Twitter</label>
                          <input
                            className={styles.input}
                            type="text"
                            placeholder="@you"
                            autoComplete="off"
                            value={local.online.x}
                            onChange={(e) => setOnline({ x: e.target.value })}
                            onBlur={runScan}
                          />
                        </div>
                      </div>

                      {scanState !== "idle" && (
                        <div
                          className={`${styles.scan} ${
                            scanState === "done" && scanResult && !scanResult.pending
                              ? styles.scanDone
                              : ""
                          }`}
                        >
                          {scanState === "scanning" ? (
                            <>
                              <span className={styles.spin} /> searching your recent posts…
                            </>
                          ) : scanResult && !scanResult.pending && scanResult.count > 0 ? (
                            <>
                              <span className={styles.ok}>✓</span>&nbsp;found{" "}
                              <b>
                                {scanResult.count} post{scanResult.count === 1 ? "" : "s"}
                              </b>{" "}
                              — timbre will learn your voice from these.
                            </>
                          ) : (
                            <>we&apos;ll pull your posts the moment the scanner&apos;s connected.</>
                          )}
                        </div>
                      )}

                      <div className={styles.srcActions}>
                        <button className={styles.ghost} type="button" onClick={() => skip("online")}>
                          no socials yet — skip
                        </button>
                        <button
                          className={styles.mini}
                          type="button"
                          onClick={() => advance("online")}
                        >
                          looks good <span className={styles.arrow}>→</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2 · RESUME */}
                <div
                  className={`${styles.src} ${open === "resume" ? styles.srcOpen : ""} ${
                    resumeShake ? "shake" : ""
                  }`}
                  onAnimationEnd={(e) => {
                    if (e.animationName.includes("shake")) setResumeShake(false);
                  }}
                >
                  <button
                    className={styles.srcHead}
                    type="button"
                    onClick={() => setOpen((c) => (c === "resume" ? null : "resume"))}
                  >
                    <span
                      className={`${styles.srcIc} ${iconActive("resume") ? styles.srcIcActive : ""}`}
                    >
                      📄
                    </span>
                    <span className={styles.srcTt}>
                      <b>add your resume</b>
                      <span>sharpens your background &amp; the only-you facts</span>
                    </span>
                    <span className={styles.srcStatus}>
                      <StatusPill id="resume" />
                    </span>
                    <span className={`${styles.caret} ${open === "resume" ? styles.caretOpen : ""}`}>
                      ▾
                    </span>
                  </button>
                  <div
                    className={`${styles.srcBody} ${open === "resume" ? styles.srcBodyOpen : ""}`}
                  >
                    <div className={styles.srcInner}>
                      <div className={styles.row}>
                        <textarea
                          className={styles.textarea}
                          rows={5}
                          placeholder="paste your resume here…"
                          value={local.docs.resume}
                          onChange={(e) => {
                            setDocs({ resume: e.target.value });
                            if (e.target.value.trim()) setResumeErr(false);
                          }}
                        />
                        <div className={styles.hint}>
                          paste it in, or dictate it with your own Wispr Flow into the box.
                        </div>
                      </div>
                      <div className={`err ${resumeErr ? "show" : ""}`}>
                        nothing loaded yet — paste, upload, or skip.
                      </div>
                      <div className={styles.srcActions}>
                        <button className={styles.ghost} type="button" onClick={() => skip("resume")}>
                          skip this
                        </button>
                        <button
                          className={styles.mini}
                          type="button"
                          onClick={() => advance("resume")}
                        >
                          add resume <span className={styles.arrow}>→</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3 · LINES */}
                <div className={`${styles.src} ${open === "lines" ? styles.srcOpen : ""}`}>
                  <button
                    className={styles.srcHead}
                    type="button"
                    onClick={() => setOpen((c) => (c === "lines" ? null : "lines"))}
                  >
                    <span
                      className={`${styles.srcIc} ${iconActive("lines") ? styles.srcIcActive : ""}`}
                    >
                      ✍️
                    </span>
                    <span className={styles.srcTt}>
                      <b>a few quick lines</b>
                      <span>three prompts — type or dictate, your call</span>
                    </span>
                    <span className={styles.srcStatus}>
                      <StatusPill id="lines" />
                    </span>
                    <span className={`${styles.caret} ${open === "lines" ? styles.caretOpen : ""}`}>
                      ▾
                    </span>
                  </button>
                  <div className={`${styles.srcBody} ${open === "lines" ? styles.srcBodyOpen : ""}`}>
                    <div className={styles.srcInner}>
                      <div className={styles.row}>
                        <label className={styles.label}>your one-liner (role + lane)</label>
                        <textarea
                          className={styles.textarea}
                          rows={2}
                          placeholder="type it, or dictate with your own Wispr Flow"
                          value={local.typed.identity}
                          onChange={(e) => setTyped({ identity: e.target.value })}
                        />
                        <div className={styles.eg}>
                          e.g. &ldquo;ai strategist at tenex — ex-athlete who got obsessed with
                          building&rdquo;
                        </div>
                      </div>
                      <div className={styles.row}>
                        <label className={styles.label}>what you&apos;re known for</label>
                        <textarea
                          className={styles.textarea}
                          rows={2}
                          placeholder="type it, or dictate with your own Wispr Flow"
                          value={local.typed.known_for}
                          onChange={(e) => setTyped({ known_for: e.target.value })}
                        />
                        <div className={styles.eg}>
                          e.g. &ldquo;shipping fast and showing the actual work — not the highlight
                          reel&rdquo;
                        </div>
                      </div>
                      <div className={styles.row}>
                        <label className={styles.label}>a belief or lesson you&apos;d defend</label>
                        <textarea
                          className={styles.textarea}
                          rows={2}
                          placeholder="type it, or dictate with your own Wispr Flow"
                          value={local.typed.beliefs}
                          onChange={(e) => setTyped({ beliefs: e.target.value })}
                        />
                        <div className={styles.eg}>
                          e.g. &ldquo;most content is slop because people skip the receipts&rdquo;
                        </div>
                      </div>
                      <div className={styles.srcActions}>
                        <button className={styles.ghost} type="button" onClick={() => skip("lines")}>
                          skip this
                        </button>
                        <button
                          className={styles.mini}
                          type="button"
                          onClick={() => advance("lines")}
                        >
                          save lines <span className={styles.arrow}>→</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className={styles.actions}>
                <button
                  className={styles.back}
                  type="button"
                  onClick={() => router.push("/onboarding/why")}
                >
                  ← back
                </button>
                <button
                  className={`cta ${busy ? "disabled" : ""}`}
                  type="button"
                  onClick={onContinue}
                >
                  {busy ? "saving…" : "next: your voice"} <span className="arrow">→</span>
                </button>
              </div>
            </section>

            {/* progress card */}
            <aside className={styles.pcard}>
              <div className={styles.pcHead}>
                <span className={styles.pcTitle}>your profile</span>
                <span className={styles.pcCount}>
                  <b>{doneCount}</b> of {checks.length}
                </span>
              </div>
              <div className={styles.pcBar}>
                <i style={{ width: `${pcPct}%` }} />
              </div>
              <ul className={styles.checklist}>
                {checks.map((c) => (
                  <li
                    key={c.label}
                    className={`${styles.citem} ${c.done ? styles.citemDone : ""}`}
                  >
                    <span className={styles.ck}>
                      <Check />
                    </span>
                    <span className={styles.lbl}>
                      {c.label}
                      {c.sub && <small>{c.sub}</small>}
                    </span>
                  </li>
                ))}
              </ul>
              <div className={styles.pcFoot}>
                <span className={styles.ring} /> everything saves as you go
              </div>
            </aside>
          </div>
        )}
      </main>
    </>
  );
}
