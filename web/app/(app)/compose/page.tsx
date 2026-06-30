"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, ApiError, type PostRecord } from "@/lib/api";
import { gateLabel, dimLabel } from "@/lib/score";
import { getName } from "@/lib/onboarding-store";
import { Waveform } from "@/components/Waveform";
import styles from "./page.module.css";

type Source = "say" | "paste";
type Phase = "idle" | "drafting" | "done";
type GateErr = null | "onboarding" | "generic";

const PLACEHOLDERS: Record<Source, string> = {
  say: "tell me what you worked on — one honest line is enough. (dictate with your own Wispr Flow into any field.)",
  paste:
    "paste your notes or a transcript — timbre reads the real work and only asks for what's missing.",
};

function Compose() {
  const searchParams = useSearchParams();
  const [work, setWork] = useState(() => searchParams.get("work") ?? "");
  const [source, setSource] = useState<Source>("say");
  const [phase, setPhase] = useState<Phase>("idle");
  const [post, setPost] = useState<PostRecord | null>(null);

  const [showErr, setShowErr] = useState(false);
  const [shake, setShake] = useState(false);
  const [gateErr, setGateErr] = useState<GateErr>(null);
  const [genericMsg, setGenericMsg] = useState("");

  const [editing, setEditing] = useState(false);
  const [editBody, setEditBody] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [approving, setApproving] = useState(false);
  const [showDims, setShowDims] = useState(false);

  const [name, setName] = useState("");
  const [tone, setTone] = useState<string[]>([]);

  useEffect(() => {
    setName(getName() || "you");
    let live = true;
    (async () => {
      try {
        const intake = await api.getIntake();
        if (live) setTone((intake.voice.tone_words ?? []).slice(0, 2));
      } catch {
        /* best-effort top chip only */
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  const initial = (name || "y").trim().charAt(0).toUpperCase();

  async function runCompose() {
    if (!work.trim()) {
      setShowErr(true);
      setShake(true);
      return;
    }
    setShowErr(false);
    setGateErr(null);
    setEditing(false);
    setPhase("drafting");
    try {
      const res = await api.compose(work.trim());
      setPost(res.post);
      setShowDims(false);
      setPhase("done");
    } catch (e) {
      setPhase("idle");
      if (e instanceof ApiError && e.status === 409) {
        setGateErr("onboarding");
      } else {
        setGateErr("generic");
        setGenericMsg(e instanceof Error ? e.message : "something went wrong.");
      }
    }
  }

  async function approve() {
    if (!post || approving) return;
    setApproving(true);
    try {
      const updated = await api.approvePost(post.id);
      setPost(updated);
    } catch (e) {
      setGateErr("generic");
      setGenericMsg(e instanceof Error ? e.message : "couldn't approve.");
    } finally {
      setApproving(false);
    }
  }

  function startEdit() {
    if (!post) return;
    setEditBody(post.body);
    setEditing(true);
  }

  async function saveEdit() {
    if (!post || savingEdit) return;
    setSavingEdit(true);
    try {
      const updated = await api.patchPost(post.id, { body: editBody, rescore: true });
      setPost(updated);
      setEditing(false);
    } catch (e) {
      setGateErr("generic");
      setGenericMsg(e instanceof Error ? e.message : "couldn't save your edit.");
    } finally {
      setSavingEdit(false);
    }
  }

  const score = post?.score;
  const qa = score ? score.quality_avg : 0;
  const barPct = Math.max(0, Math.min(100, (qa / 10) * 100));
  const approved = post?.status === "approved";

  return (
    <>
      <div className={styles.top}>
        <h1>write a post</h1>
        <div className={styles.vchip}>
          <span className={styles.d} /> writing as <b>your voice</b>
          {tone.length > 0 && ` · ${tone.join(" · ")}`}
        </div>
      </div>

      <div className={styles.content}>
        {/* input */}
        <div
          className={`${styles.incard}${shake ? " shake" : ""}`}
          onAnimationEnd={() => setShake(false)}
        >
          <div className={styles.inhead}>
            <span className={styles.t}>what did you do?</span>
            <div className={styles.srcpills}>
              <button
                type="button"
                className={`${styles.spill}${source === "say" ? " " + styles.spillon : ""}`}
                onClick={() => setSource("say")}
              >
                say it
              </button>
              <button
                type="button"
                className={`${styles.spill}${source === "paste" ? " " + styles.spillon : ""}`}
                onClick={() => setSource("paste")}
              >
                paste notes
              </button>
            </div>
          </div>
          <textarea
            className={styles.area}
            value={work}
            placeholder={PLACEHOLDERS[source]}
            onChange={(e) => {
              setWork(e.target.value);
              if (e.target.value.trim()) setShowErr(false);
            }}
          />
          <div className={styles.inrow}>
            <span className={styles.hint}>
              🔒 stays on your machine · timbre never posts without you
            </span>
            <button
              className={styles.draftbtn}
              type="button"
              onClick={runCompose}
              disabled={phase === "drafting"}
            >
              {phase === "drafting" ? "drafting…" : "draft it in my voice →"}
            </button>
          </div>
          <div className={`err${showErr ? " show" : ""}`}>
            tell me what you did first — even one line.
          </div>
        </div>

        {/* onboarding gate */}
        {gateErr === "onboarding" && (
          <div className={styles.gate}>
            <h3>finish onboarding first</h3>
            <p>
              timbre needs your voice profile before it can draft in your voice. it only
              takes a few minutes — then come back and ship.
            </p>
            <Link href="/onboarding/why" className="cta">
              tune my voice <span className="arrow">→</span>
            </Link>
          </div>
        )}

        {/* generic error */}
        {gateErr === "generic" && (
          <div className={styles.gate}>
            <h3>that didn&apos;t go through</h3>
            <p>{genericMsg || "something went wrong. give it another go."}</p>
            <button className="cta" type="button" onClick={runCompose}>
              try again <span className="arrow">→</span>
            </button>
          </div>
        )}

        {/* drafting loader */}
        {phase === "drafting" && (
          <div className={styles.drafting}>
            <div className={styles.draftbars}>
              <Waveform bars={22} />
            </div>
            <div className={styles.dt}>writing it the way you&apos;d say it…</div>
          </div>
        )}

        {/* result */}
        {phase === "done" && post && score && (
          <div className={styles.result}>
            <div className={styles.postcard}>
              <div className={styles.ph}>
                <span className={styles.av}>{initial}</span>
                <span>
                  <span className={styles.nm}>{name}</span>
                  <br />
                  <span className={styles.meta}>
                    {post.status} · in your voice
                  </span>
                </span>
              </div>

              {editing ? (
                <textarea
                  className={styles.editarea}
                  value={editBody}
                  onChange={(e) => setEditBody(e.target.value)}
                />
              ) : (
                <div className={styles.body}>{post.body}</div>
              )}

              {(post.proof.length > 0 || post.redactions.length > 0) && (
                <div className={styles.receipts}>
                  <div className={styles.rl}>↳ receipts (pulled from your work)</div>
                  {post.proof.length > 0 && (
                    <div className={styles.rcs}>
                      {post.proof.map((p, i) => (
                        <span key={i} className="chiprc">
                          <span className="ic">▪</span> {p}
                        </span>
                      ))}
                    </div>
                  )}
                  {post.redactions.length > 0 && (
                    <div className={styles.redaction}>
                      redacted: {post.redactions.join(", ")}
                    </div>
                  )}
                </div>
              )}

              <div className={styles.pa}>
                {editing ? (
                  <>
                    <button
                      className={`${styles.pbtn} ${styles.primary}`}
                      type="button"
                      onClick={saveEdit}
                      disabled={savingEdit}
                    >
                      {savingEdit ? "saving…" : "save edits"}
                    </button>
                    <button
                      className={`${styles.pbtn} ${styles.ghost}`}
                      type="button"
                      onClick={() => setEditing(false)}
                    >
                      cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className={`${styles.pbtn} ${styles.primary}`}
                      type="button"
                      onClick={approve}
                      disabled={approving || approved}
                    >
                      {approved ? "approved ✓" : approving ? "approving…" : "approve draft"}
                    </button>
                    <button
                      className={`${styles.pbtn} ${styles.ghost}`}
                      type="button"
                      onClick={startEdit}
                    >
                      edit
                    </button>
                    <button
                      className={`${styles.pbtn} ${styles.ghost}`}
                      type="button"
                      onClick={runCompose}
                    >
                      regenerate
                    </button>
                  </>
                )}
              </div>

              {approved && (
                <div className={styles.approved}>
                  <span>✓</span> approved — drafts only; this never posts anywhere.
                </div>
              )}
            </div>

            {/* eval */}
            <aside className={styles.eval}>
              <div className={styles.et}>eval</div>
              <div className={styles.score}>
                <span className={styles.scoren}>{qa.toFixed(1)}</span>
                <span className={styles.scoreo}>/ 10</span>
              </div>
              <div className={styles.ebar}>
                <i style={{ width: `${barPct}%` }} />
              </div>

              <div className={styles.gates}>
                {score.gates.map((g) => (
                  <div
                    key={g.name}
                    className={`${styles.gaterow}${g.passed ? "" : " " + styles.fail}`}
                    title={g.reason}
                  >
                    <span className={styles.gk}>{g.passed ? "✓" : ""}</span>
                    {gateLabel(g.name)}
                  </div>
                ))}
              </div>

              <button
                className={styles.dimtoggle}
                type="button"
                onClick={() => setShowDims((v) => !v)}
              >
                {showDims ? "hide dimensions ▲" : "show all 9 dimensions ▾"}
              </button>
              {showDims && (
                <div className={styles.dims}>
                  {score.dimensions.map((d) => (
                    <div key={d.name} className={styles.dim} title={d.reason}>
                      <div className={styles.dimhead}>
                        <span className={styles.dimlabel}>{dimLabel(d.name)}</span>
                        <span className={styles.dimscore}>{d.score.toFixed(1)}/10</span>
                      </div>
                      <div className={styles.dimbar}>
                        <i
                          style={{
                            width: `${Math.max(0, Math.min(100, (d.score / 10) * 100))}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className={styles.gatenote}>
                {score.gates_passed}/{score.gates_total} gates passed. the score is your
                meter — not a gate. edit freely; it re-scores.
              </div>
            </aside>
          </div>
        )}
      </div>
    </>
  );
}

export default function ComposePage() {
  return (
    <Suspense
      fallback={
        <div className={styles.content}>
          <div className={styles.drafting}>
            <div className={styles.dt}>loading…</div>
          </div>
        </div>
      }
    >
      <Compose />
    </Suspense>
  );
}
