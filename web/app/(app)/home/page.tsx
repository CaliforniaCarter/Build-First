"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type PostRecord, type Take } from "@/lib/api";
import { getName, elapsedLabel } from "@/lib/onboarding-store";
import styles from "./page.module.css";

// Plain, static writing prompts. NOT AI-generated — they just prefill the box.
const STARTERS: { k: string; q: string }[] = [
  { k: "show your work", q: "the thing i shipped today and what it took" },
  { k: "a hot take", q: "an opinion about my work i'd actually defend" },
  { k: "what i learned", q: "a lesson from this week i didn't expect" },
];

function timeOfDay(d: Date): string {
  const h = d.getHours();
  if (h < 12) return "morning";
  if (h < 18) return "afternoon";
  return "evening";
}

// Best-effort: pull a few tone descriptors out of the persona doc when intake
// has no tone words yet. Returns [] if nothing parseable (never invents).
function deriveTone(personaMd: string): string[] {
  for (const line of personaMd.split("\n")) {
    const m = line.match(/(?:tone|voice)\s*(?:words)?\s*[:\-—]\s*(.+)/i);
    if (m) {
      return m[1]
        .split(/[,;·•/]/)
        .map((s) => s.trim().replace(/[.*_`"']/g, ""))
        .filter((s) => s.length > 1 && s.length < 24)
        .slice(0, 5);
    }
  }
  return [];
}

export default function HomePage() {
  const router = useRouter();
  const [name, setLocalName] = useState("");
  const [tod, setTod] = useState("");
  const [text, setText] = useState("");
  const [posts, setPosts] = useState<PostRecord[] | null>(null);
  const [tone, setTone] = useState<string[]>([]);
  const [toTuned, setToTuned] = useState("—");
  // takes are a live LLM call — loaded on demand so they never slow the dashboard.
  const [takes, setTakes] = useState<Take[] | null>(null);
  const [takesState, setTakesState] = useState<"idle" | "loading" | "error">("idle");

  useEffect(() => {
    setLocalName(getName() || "there");
    setTod(timeOfDay(new Date()));
    setToTuned(elapsedLabel());

    let live = true;
    (async () => {
      try {
        const { posts } = await api.listPosts();
        if (live) setPosts(posts);
      } catch {
        if (live) setPosts([]);
      }
      try {
        const intake = await api.getIntake();
        let words = intake.voice.tone_words ?? [];
        if (words.length === 0) {
          try {
            const docs = await api.getDocs();
            words = deriveTone(docs.persona_md ?? "");
          } catch {
            /* no persona yet */
          }
        }
        if (live) setTone(words);
      } catch {
        /* intake unavailable — leave tone empty */
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  const drafts = useMemo(
    () => (posts ?? []).filter((p) => p.status === "draft").length,
    [posts]
  );
  const approved = useMemo(
    () => (posts ?? []).filter((p) => p.status === "approved").length,
    [posts]
  );
  const recent = (posts ?? []).slice(0, 3);

  function go() {
    const t = text.trim();
    router.push(t ? `/compose?work=${encodeURIComponent(t)}` : "/compose");
  }

  async function loadTakes() {
    if (takesState === "loading") return;
    setTakesState("loading");
    try {
      const { takes } = await api.getTakes();
      setTakes(takes);
      setTakesState("idle");
    } catch {
      setTakesState("error");
    }
  }

  // Seed the compose box with a take, then bring it back into view up top.
  function seedTake(t: Take) {
    setText(t.take);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className={styles.main}>
      <div className={styles.head}>
        <div className={styles.greet}>
          good {tod || "day"}
          {name && ", "}
          <span className={styles.hl}>{name ? `${name}.` : ""}</span>
        </div>
        <div className={styles.sub}>
          drop in what you did today — timbre writes it in your voice.
        </div>
      </div>

      <div className={styles.layout}>
        <div>
          {/* write box */}
          <div className={styles.writebox}>
            <div className={styles.wt}>what did you ship today?</div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === "Enter") go();
              }}
              placeholder="one honest line is enough — or paste your notes. (dictate with your own Wispr Flow into any field.)"
            />
            <div className={styles.wr}>
              <span className={styles.lock}>
                🔒 stays on your machine · drafts only
              </span>
              <button className={styles.go} onClick={go} type="button">
                draft it in my voice <span className={styles.ar}>→</span>
              </button>
            </div>
          </div>

          {/* starters — plain static prompts, clearly not AI suggestions */}
          <div className={styles.sectt}>
            starters
            <span className={styles.note}>prompts to get you going — pick one to prefill</span>
          </div>
          <div className={styles.suggest}>
            {STARTERS.map((s) => (
              <button
                key={s.k}
                className={styles.sug}
                type="button"
                onClick={() => setText(s.q)}
              >
                <div className={styles.sugk}>{s.k}</div>
                <div className={styles.sugq}>{s.q}</div>
              </button>
            ))}
          </div>

          {/* takes forming — spiky opinions grounded in your work (live, on-demand) */}
          <div className={styles.sectt}>
            takes forming
            <span className={styles.note}>opinions you&apos;re starting to form — tap one to draft it</span>
          </div>
          {takes === null ? (
            <div className={styles.takesidle}>
              {takesState === "error" ? (
                <span>
                  couldn&apos;t form takes just now —{" "}
                  <button type="button" onClick={loadTakes}>
                    try again
                  </button>
                </span>
              ) : (
                <button
                  className={styles.formtakes}
                  type="button"
                  onClick={loadTakes}
                  disabled={takesState === "loading"}
                >
                  {takesState === "loading" ? "forming…" : "form takes from my work →"}
                </button>
              )}
            </div>
          ) : takes.length === 0 ? (
            <div className={styles.empty}>
              no takes yet — write a few posts and they&apos;ll start forming.
            </div>
          ) : (
            <div className={styles.takes}>
              {takes.map((t, i) => (
                <button
                  key={i}
                  className={styles.take}
                  type="button"
                  onClick={() => seedTake(t)}
                >
                  <span className={styles.takeq}>{t.take}</span>
                  <span className={styles.takebo}>↳ {t.based_on}</span>
                </button>
              ))}
            </div>
          )}

          {/* recent posts */}
          <div className={styles.sectt}>recent</div>
          {posts === null ? (
            <div className={styles.empty}>loading your posts…</div>
          ) : recent.length === 0 ? (
            <div className={styles.empty}>
              no posts yet — <Link href="/compose">write your first →</Link>
            </div>
          ) : (
            <>
              <div className={styles.posts}>
                {recent.map((p) => (
                  <Link key={p.id} href="/feed" className={styles.post}>
                    <span className={styles.postbody}>{p.body}</span>
                    <span
                      className={`${styles.badge} ${
                        p.status === "draft" ? styles.draft : styles.appr
                      }`}
                    >
                      {p.status}
                    </span>
                    <span className={styles.sc}>
                      {p.score.quality_avg.toFixed(1)}
                    </span>
                  </Link>
                ))}
              </div>
              <Link href="/feed" className={styles.seeall}>
                see all posts →
              </Link>
            </>
          )}
        </div>

        {/* right rail */}
        <aside className={styles.rail}>
          <div className={styles.vcard}>
            <div className={styles.vt}>
              <span>your voice</span>
              <Link href="/profile">edit →</Link>
            </div>
            {tone.length > 0 ? (
              <div className={styles.vchips}>
                {tone.map((w) => (
                  <span key={w} className={styles.vchip}>
                    {w}
                  </span>
                ))}
              </div>
            ) : (
              <div className={styles.vempty}>
                no tone words yet — <Link href="/profile">tune your voice →</Link>
              </div>
            )}
            <div className={styles.tuned}>
              <span className={styles.pip} /> timbre writes like this
            </div>
          </div>

          <div className={styles.stat}>
            <div>
              <div className={styles.statn}>{drafts}</div>
              <div className={styles.statl}>drafts</div>
            </div>
            <div>
              <div className={styles.statn}>{approved}</div>
              <div className={styles.statl}>approved</div>
            </div>
            <div>
              <div className={styles.statn}>{toTuned}</div>
              <div className={styles.statl}>to tuned</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
