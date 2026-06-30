"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, type PostRecord } from "@/lib/api";
import { getName } from "@/lib/onboarding-store";

type Tab = "all" | "drafts" | "approved";

// honest relative timestamp — no faked "today · 2:14 pm"
function timeAgo(iso: string): string {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "";
  const s = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (s < 45) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  const w = Math.floor(d / 7);
  if (w < 5) return `${w}w ago`;
  const mo = Math.floor(d / 30);
  if (mo < 12) return `${mo}mo ago`;
  return `${Math.floor(d / 365)}y ago`;
}

const AV_STYLE: React.CSSProperties = {
  background: "linear-gradient(135deg,#FFE500,#FFB200)",
  color: "#0B0B0C",
  fontFamily: "var(--display)",
};

export default function FeedPage() {
  const [posts, setPosts] = useState<PostRecord[] | null>(null);
  const [tab, setTab] = useState<Tab>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [name, setName] = useState("you");

  useEffect(() => setName(getName() || "you"), []);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const { posts: loaded } = await api.listPosts();
        if (live) setPosts(loaded);
      } catch (e) {
        if (!live) return;
        if (e instanceof ApiError && e.status === 409) setNeedsOnboarding(true);
        else setError(e instanceof Error ? e.message : "couldn't load your posts.");
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  const initial = (name || "y").trim().charAt(0).toUpperCase();
  const all = posts ?? [];
  const drafts = all.filter((p) => p.status === "draft");
  const approved = all.filter((p) => p.status === "approved");
  const shown = tab === "drafts" ? drafts : tab === "approved" ? approved : all;

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: "all", label: "all", count: all.length },
    { key: "drafts", label: "drafts", count: drafts.length },
    { key: "approved", label: "approved", count: approved.length },
  ];

  return (
    <div className="px-6 md:px-11 pt-9 pb-16">
      <div className="flex items-center justify-between mb-6 max-w-[860px]">
        <h1 className="serif text-[38px]">posts</h1>
        <Link href="/compose" className="cta">
          + new post
        </Link>
      </div>

      {loading && (
        <p className="text-[14px]" style={{ color: "var(--muted)" }}>
          loading your posts…
        </p>
      )}

      {!loading && needsOnboarding && (
        <div className="card max-w-[560px]">
          <div className="font-[var(--display)] font-semibold text-[17px] mb-2">
            finish onboarding first
          </div>
          <p className="text-[14px] mb-5" style={{ color: "var(--muted)" }}>
            timbre needs your voice profile before it can draft posts. it takes about 8
            minutes.
          </p>
          <Link href="/onboarding/why" className="cta">
            tune my voice <span className="arrow">→</span>
          </Link>
        </div>
      )}

      {!loading && !needsOnboarding && error && (
        <div className="card max-w-[560px]">
          <div className="font-[var(--display)] font-semibold text-[17px] mb-2">
            couldn&apos;t load posts
          </div>
          <p className="text-[14px]" style={{ color: "var(--bad)" }}>
            {error}
          </p>
        </div>
      )}

      {!loading && !needsOnboarding && !error && posts && (
        <>
          <div className="flex gap-2 mb-5">
            {tabs.map((t) => {
              const on = tab === t.key;
              return (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setTab(t.key)}
                  className="text-[13px] px-[15px] py-2 rounded-full transition-colors"
                  style={{
                    background: on ? "#16160c" : "transparent",
                    color: on ? "var(--ink)" : "var(--muted)",
                    border: `1px solid ${on ? "#3a3a22" : "var(--border)"}`,
                  }}
                >
                  {t.label} · {t.count}
                </button>
              );
            })}
          </div>

          {all.length === 0 ? (
            <div className="card max-w-[560px] text-center py-10">
              <div className="serif text-[26px] mb-2">no posts yet</div>
              <p className="text-[14px] mb-6 max-w-[36ch] mx-auto" style={{ color: "var(--muted)" }}>
                drop in what you actually worked on — timbre drafts the post in your voice.
              </p>
              <Link href="/compose" className="cta">
                write your first post <span className="arrow">→</span>
              </Link>
            </div>
          ) : shown.length === 0 ? (
            <p className="text-[14px] max-w-[860px]" style={{ color: "var(--dim)" }}>
              nothing in {tab} yet.
            </p>
          ) : (
            <div className="flex flex-col gap-3 max-w-[860px]">
              {shown.map((post) => {
                const appr = post.status === "approved";
                return (
                  <article
                    key={post.id}
                    className="p-5 rounded-2xl"
                    style={{ background: "var(--card)", border: "1px solid var(--border)" }}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span
                        className="grid place-items-center w-[34px] h-[34px] rounded-full font-bold text-[13px]"
                        style={AV_STYLE}
                      >
                        {initial}
                      </span>
                      <span className="leading-tight">
                        <span className="block text-[13.5px] font-semibold">{name}</span>
                        <span className="block text-[11.5px]" style={{ color: "var(--dim)" }}>
                          {timeAgo(post.created_at)}
                          {post.topic ? ` · ${post.topic}` : ""}
                        </span>
                      </span>
                      <span className="ml-auto flex items-center gap-3">
                        <span
                          className="text-[11px] font-semibold px-[11px] py-1 rounded-full"
                          style={
                            appr
                              ? {
                                  background: "#16160c",
                                  color: "var(--yellow)",
                                  border: "1px solid #3a3a22",
                                  fontFamily: "var(--display)",
                                }
                              : {
                                  background: "#1a1a1e",
                                  color: "var(--muted)",
                                  border: "1px solid var(--border-hi)",
                                  fontFamily: "var(--display)",
                                }
                          }
                        >
                          {post.status}
                        </span>
                        <span
                          className="font-bold text-[13px]"
                          style={{ color: "var(--yellow)", fontFamily: "var(--display)" }}
                          title="quality score (avg of 9 dimensions)"
                        >
                          {post.score.quality_avg.toFixed(1)}
                        </span>
                      </span>
                    </div>

                    <p
                      className="text-[14px] line-clamp-3"
                      style={{ color: "#D8D8D2", lineHeight: 1.55 }}
                    >
                      {post.body}
                    </p>

                    {(post.proof.length > 0 || post.redactions.length > 0) && (
                      <div className="mt-3 flex gap-2 flex-wrap">
                        {post.proof.map((pf, i) => (
                          <span key={i} className="chiprc">
                            <span className="ic">✓</span> {pf}
                          </span>
                        ))}
                        {post.redactions.length > 0 && (
                          <span
                            className="chiprc"
                            title="sensitive details removed before drafting"
                          >
                            <span className="ic">⊘</span> redacted: {post.redactions.join(", ")}
                          </span>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
