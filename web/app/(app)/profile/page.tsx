"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Intake } from "@/lib/intake";

interface Docs {
  persona_md: string;
  profile_md: string;
  context_md: string;
}

// ── tiny inline markdown → JSX (headings / lists / paragraphs / **bold**) ─────
function inline(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) => {
    const m = /^\*\*([^*]+)\*\*$/.exec(p);
    return m ? (
      <strong key={i} style={{ color: "var(--ink)", fontWeight: 600 }}>
        {m[1]}
      </strong>
    ) : (
      <span key={i}>{p}</span>
    );
  });
}

function renderMarkdown(md: string): React.ReactNode[] {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];
  let para: string[] = [];

  const flushList = () => {
    if (!list.length) return;
    const items = list;
    list = [];
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc pl-5 my-2 flex flex-col gap-1">
        {items.map((it, i) => (
          <li key={i} className="text-[14px]" style={{ color: "#D8D8D2", lineHeight: 1.55 }}>
            {inline(it)}
          </li>
        ))}
      </ul>
    );
  };
  const flushPara = () => {
    if (!para.length) return;
    const text = para.join(" ");
    para = [];
    blocks.push(
      <p
        key={`p-${blocks.length}`}
        className="text-[14px] my-2"
        style={{ color: "#D8D8D2", lineHeight: 1.6 }}
      >
        {inline(text)}
      </p>
    );
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const h = /^(#{1,3})\s+(.*)$/.exec(line);
    const li = /^[-*]\s+(.*)$/.exec(line.trim());
    if (h) {
      flushList();
      flushPara();
      const level = h[1].length;
      blocks.push(
        <div
          key={`h-${blocks.length}`}
          className="font-[var(--display)] font-semibold mt-4 mb-1 first:mt-0"
          style={{
            fontSize: level === 1 ? "16px" : "11px",
            color: level === 1 ? "var(--ink)" : "var(--dim)",
            letterSpacing: level > 1 ? "0.08em" : undefined,
            textTransform: level > 1 ? "uppercase" : undefined,
          }}
        >
          {h[2]}
        </div>
      );
    } else if (li) {
      flushPara();
      list.push(li[1]);
    } else if (line.trim() === "") {
      flushList();
      flushPara();
    } else {
      flushList();
      para.push(line.trim());
    }
  }
  flushList();
  flushPara();
  return blocks;
}

// pull a real count out of the free-form existing_posts field; null if none known
function postsFound(i: Intake): number | null {
  const m = /\d+/.exec(i.online.existing_posts || "");
  return m ? parseInt(m[0], 10) : null;
}

export default function ProfilePage() {
  const [docs, setDocs] = useState<Docs | null>(null);
  const [intake, setIntake] = useState<Intake | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  // persona.md — free-form, safe to overwrite directly
  const [editingPersona, setEditingPersona] = useState(false);
  const [personaDraft, setPersonaDraft] = useState("");
  const [savingPersona, setSavingPersona] = useState(false);
  const [personaErr, setPersonaErr] = useState<string | null>(null);

  // profile.md — REGENERATED, so we edit the underlying intake fields
  const [editingWho, setEditingWho] = useState(false);
  const [who, setWho] = useState({ identity: "", known_for: "", beliefs: "", linkedin: "", x: "" });
  const [savingWho, setSavingWho] = useState(false);
  const [whoErr, setWhoErr] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const d = await api.getDocs();
        const i = await api.getIntake();
        if (!live) return;
        setDocs(d);
        setIntake(i);
      } catch (e) {
        if (!live) return;
        if (e instanceof ApiError && e.status === 409) setNeedsOnboarding(true);
        else setError(e instanceof Error ? e.message : "couldn't load your voice profile.");
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  async function savePersona() {
    setSavingPersona(true);
    setPersonaErr(null);
    try {
      await api.putPersonaDoc(personaDraft);
      setDocs((d) => (d ? { ...d, persona_md: personaDraft } : d));
      setEditingPersona(false);
    } catch (e) {
      setPersonaErr(e instanceof Error ? e.message : "couldn't save.");
    } finally {
      setSavingPersona(false);
    }
  }

  function openWho() {
    if (!intake) return;
    setWho({
      identity: intake.typed.identity,
      known_for: intake.typed.known_for,
      beliefs: intake.typed.beliefs,
      linkedin: intake.online.linkedin,
      x: intake.online.x,
    });
    setWhoErr(null);
    setEditingWho(true);
  }

  async function saveWho() {
    setSavingWho(true);
    setWhoErr(null);
    try {
      const { intake: updated } = await api.patchIntake({
        typed: { identity: who.identity, known_for: who.known_for, beliefs: who.beliefs },
        online: { linkedin: who.linkedin, x: who.x },
      });
      // profile.md is deterministic — rebuild it from the new fields
      const built = await api.buildProfile();
      setIntake(updated);
      setDocs((d) =>
        d ? { ...d, profile_md: built.profile_md, context_md: built.context_md } : d
      );
      setEditingWho(false);
    } catch (e) {
      setWhoErr(e instanceof Error ? e.message : "couldn't save.");
    } finally {
      setSavingWho(false);
    }
  }

  return (
    <div className="px-6 md:px-11 pt-9 pb-16">
      <div className="flex items-center justify-between mb-1.5 max-w-[860px]">
        <h1 className="serif text-[38px]">your voice profile</h1>
        <Link
          href="/onboarding/voice"
          className="font-[var(--display)] font-semibold text-[13.5px] px-4 py-2.5 rounded-xl transition-colors"
          style={{ border: "1px solid var(--border-hi)", color: "var(--ink)" }}
        >
          ⌁ re-tune
        </Link>
      </div>
      <div
        className="flex items-center gap-2.5 mb-6 text-[14px] max-w-[860px]"
        style={{ color: "var(--muted)" }}
      >
        <span
          className="w-[7px] h-[7px] rounded-full shrink-0"
          style={{ background: "var(--yellow)", boxShadow: "0 0 7px var(--yellow)" }}
        />
        this is how timbre writes. change anything — it re-learns instantly. nothing leaves your
        machine.
      </div>

      {loading && (
        <p className="text-[14px]" style={{ color: "var(--muted)" }}>
          loading your voice profile…
        </p>
      )}

      {!loading && needsOnboarding && (
        <div className="card max-w-[560px]">
          <div className="font-[var(--display)] font-semibold text-[17px] mb-2">
            finish onboarding first
          </div>
          <p className="text-[14px] mb-5" style={{ color: "var(--muted)" }}>
            there&apos;s no voice profile yet — let&apos;s tune one. it takes about 8 minutes.
          </p>
          <Link href="/onboarding/why" className="cta">
            tune my voice <span className="arrow">→</span>
          </Link>
        </div>
      )}

      {!loading && !needsOnboarding && error && (
        <div className="card max-w-[560px]">
          <div className="font-[var(--display)] font-semibold text-[17px] mb-2">
            couldn&apos;t load profile
          </div>
          <p className="text-[14px]" style={{ color: "var(--bad)" }}>
            {error}
          </p>
        </div>
      )}

      {!loading && !needsOnboarding && !error && docs && intake && (
        <div className="flex flex-col gap-[18px] max-w-[860px]">
          {/* ── your voice · persona.md ───────────────────────────────── */}
          <section
            className="card"
            style={{
              background: "linear-gradient(180deg,#16160e,#121214 30%)",
              borderColor: "var(--border-hi)",
            }}
          >
            <div className="flex items-center justify-between">
              <div
                className="font-[var(--display)] font-semibold text-[14px]"
                style={{ color: "var(--muted)" }}
              >
                your voice{" "}
                <span className="text-[11px]" style={{ color: "var(--dim)" }}>
                  · persona.md
                </span>
              </div>
              {!editingPersona && (
                <button
                  type="button"
                  onClick={() => {
                    setPersonaDraft(docs.persona_md);
                    setPersonaErr(null);
                    setEditingPersona(true);
                  }}
                  className="text-[12px] transition-colors hover:text-[var(--yellow)]"
                  style={{ color: "var(--muted)" }}
                >
                  edit
                </button>
              )}
            </div>

            {/* signature line built from real tone words */}
            {intake.voice.tone_words.length > 0 && !editingPersona && (
              <div
                className="serif"
                style={{ fontSize: "clamp(24px,3vw,32px)", lineHeight: 1.1, margin: "14px 0 18px" }}
              >
                {intake.voice.tone_words.slice(0, 3).map((t, i, arr) =>
                  i < arr.length - 1 ? (
                    <span key={i}>{t} · </span>
                  ) : (
                    <span key={i} className="hl">
                      {t}.
                    </span>
                  )
                )}
              </div>
            )}

            {editingPersona ? (
              <div className="mt-3">
                <p className="text-[12.5px] mb-2" style={{ color: "var(--dim)" }}>
                  persona.md is a plain file you own — edit it directly.
                </p>
                <textarea
                  className="tn"
                  rows={16}
                  value={personaDraft}
                  onChange={(e) => setPersonaDraft(e.target.value)}
                  style={{ fontFamily: "var(--body)", lineHeight: 1.55 }}
                />
                {personaErr && (
                  <p className="mt-2 text-[13px]" style={{ color: "var(--bad)" }}>
                    {personaErr}
                  </p>
                )}
                <div className="flex gap-2.5 mt-3">
                  <button
                    type="button"
                    className={`cta ${savingPersona ? "disabled" : ""}`}
                    onClick={savePersona}
                  >
                    {savingPersona ? "saving…" : "save"}
                  </button>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => setEditingPersona(false)}
                  >
                    cancel
                  </button>
                </div>
              </div>
            ) : docs.persona_md.trim() ? (
              <PersonaView md={docs.persona_md} />
            ) : (
              <p className="mt-3 text-[14px]" style={{ color: "var(--dim)" }}>
                your voice hasn&apos;t been generated yet — re-tune to build it.
              </p>
            )}
          </section>

          {/* ── who you are · profile.md (regenerated from intake) ────── */}
          <section className="card">
            <div className="flex items-center justify-between">
              <div
                className="font-[var(--display)] font-semibold text-[14px]"
                style={{ color: "var(--muted)" }}
              >
                who you are{" "}
                <span className="text-[11px]" style={{ color: "var(--dim)" }}>
                  · profile.md
                </span>
              </div>
              {!editingWho && (
                <button
                  type="button"
                  onClick={openWho}
                  className="text-[12px] transition-colors hover:text-[var(--yellow)]"
                  style={{ color: "var(--muted)" }}
                >
                  edit
                </button>
              )}
            </div>

            {editingWho ? (
              <div className="mt-4 flex flex-col gap-3.5">
                <p className="text-[12.5px]" style={{ color: "var(--dim)" }}>
                  profile.md is generated from these fields — edit them and timbre rebuilds it.
                </p>
                {(
                  [
                    ["identity", "identity", "ai strategist at tenex — ex-athlete who got obsessed with building."],
                    ["known for", "known_for", "shipping fast and showing the work, not the highlight reel."],
                    ["belief", "beliefs", "most content is slop because people skip the receipts."],
                    ["linkedin", "linkedin", "linkedin.com/in/you"],
                    ["x", "x", "@you"],
                  ] as const
                ).map(([label, key, ph]) => (
                  <label key={key} className="block">
                    <span
                      className="block text-[11px] uppercase font-semibold mb-1.5"
                      style={{ color: "var(--dim)", letterSpacing: "0.08em", fontFamily: "var(--display)" }}
                    >
                      {label}
                    </span>
                    <input
                      className="tn"
                      type="text"
                      placeholder={ph}
                      value={who[key]}
                      onChange={(e) => setWho((w) => ({ ...w, [key]: e.target.value }))}
                    />
                  </label>
                ))}
                {whoErr && (
                  <p className="text-[13px]" style={{ color: "var(--bad)" }}>
                    {whoErr}
                  </p>
                )}
                <div className="flex gap-2.5">
                  <button
                    type="button"
                    className={`cta ${savingWho ? "disabled" : ""}`}
                    onClick={saveWho}
                  >
                    {savingWho ? "rebuilding…" : "save & rebuild"}
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => setEditingWho(false)}>
                    cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-1">
                <Row label="identity" value={intake.typed.identity} />
                <Row label="known for" value={intake.typed.known_for} />
                <LinksRow intake={intake} />
                <Row label="belief" value={intake.typed.beliefs} />
              </div>
            )}
          </section>

          <div
            className="text-[12.5px] flex items-center gap-2"
            style={{ color: "var(--dim)" }}
          >
            🔒 persona.md &amp; profile.md live on your machine — plain files you own.
          </div>
        </div>
      )}
    </div>
  );
}

// Split the rewritten persona.md into its `##` sections so the read view is scannable
// (a clean label · content list) instead of one undifferentiated wall of text.
function parsePersona(md: string): {
  intro: string[];
  sections: { title: string; body: string[] }[];
} {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const intro: string[] = [];
  const sections: { title: string; body: string[] }[] = [];
  let cur: { title: string; body: string[] } | null = null;
  for (const raw of lines) {
    const line = raw.trimEnd();
    const h2 = /^##\s+(.*)$/.exec(line);
    if (h2) {
      cur = { title: h2[1].trim(), body: [] };
      sections.push(cur);
    } else if (cur) {
      cur.body.push(line);
    } else if (/^#\s+/.test(line)) {
      // drop the top-level title — the serif signature line above already names the voice
      continue;
    } else {
      intro.push(line);
    }
  }
  return { intro, sections };
}

function PersonaView({ md }: { md: string }) {
  const { intro, sections } = parsePersona(md);
  // older persona format with no ## sections — fall back to the plain renderer
  if (sections.length === 0) return <div className="mt-2">{renderMarkdown(md)}</div>;
  const introText = intro.join("\n").trim();
  return (
    <div className="mt-2">
      {introText && <div className="mb-1">{renderMarkdown(introText)}</div>}
      {sections.map((s, i) => {
        const banned = /bann|never|off.?limit|avoid|don'?t/i.test(s.title);
        return (
          <div
            key={i}
            className="grid grid-cols-[150px_1fr] gap-4 items-start py-3.5"
            style={{ borderTop: "1px solid var(--border)" }}
          >
            <span
              className="text-[11px] uppercase font-semibold pt-1"
              style={{
                color: banned ? "var(--bad)" : "var(--yellow)",
                letterSpacing: "0.08em",
                fontFamily: "var(--display)",
              }}
            >
              {s.title}
            </span>
            <div className="min-w-0">{renderMarkdown(s.body.join("\n"))}</div>
          </div>
        );
      })}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="grid grid-cols-[160px_1fr] gap-4 items-start py-3.5"
      style={{ borderTop: "1px solid var(--border)" }}
    >
      <span
        className="text-[11px] uppercase font-semibold pt-0.5"
        style={{ color: "var(--dim)", letterSpacing: "0.08em", fontFamily: "var(--display)" }}
      >
        {label}
      </span>
      <span className="text-[14px]" style={{ color: value.trim() ? "var(--ink)" : "var(--dim)", lineHeight: 1.5 }}>
        {value.trim() || "—"}
      </span>
    </div>
  );
}

function LinksRow({ intake }: { intake: Intake }) {
  const links = [intake.online.linkedin, intake.online.x].filter((s) => s.trim());
  const found = postsFound(intake);
  return (
    <div
      className="grid grid-cols-[160px_1fr] gap-4 items-start py-3.5"
      style={{ borderTop: "1px solid var(--border)" }}
    >
      <span
        className="text-[11px] uppercase font-semibold pt-0.5"
        style={{ color: "var(--dim)", letterSpacing: "0.08em", fontFamily: "var(--display)" }}
      >
        links
      </span>
      <span className="text-[14px]">
        <span style={{ color: links.length ? "var(--ink)" : "var(--dim)" }}>
          {links.length ? links.join(" · ") : "no links yet"}
        </span>
        <span className="block mt-1 text-[12px]" style={{ color: "var(--dim)" }}>
          {found != null
            ? `${found} posts found`
            : "scanner pending — we'll pull your posts the moment it's connected."}
        </span>
      </span>
    </div>
  );
}
