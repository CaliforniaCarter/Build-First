"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError, type PostRecord } from "@/lib/api";
import { EvalPanel } from "@/components/EvalPanel";
import { timeAgo } from "@/lib/time";
import styles from "./page.module.css";

function titleOf(post: PostRecord): string {
  const t = (post.topic ?? "").trim();
  if (t) return t;
  const first = (post.body.split("\n").find((l) => l.trim()) ?? "").trim();
  return first || "untitled";
}

export default function PostDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [post, setPost] = useState<PostRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!id) return;
    let live = true;
    (async () => {
      try {
        const p = await api.getPost(id);
        if (live) setPost(p);
      } catch (e) {
        if (!live) return;
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
        else setError(e instanceof Error ? e.message : "couldn't load this post.");
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, [id]);

  return (
    <div className={styles.page}>
      <Link href="/feed" className={styles.back}>
        ← all posts
      </Link>

      {loading && (
        <p className="text-[14px]" style={{ color: "var(--muted)" }}>
          loading…
        </p>
      )}

      {!loading && notFound && (
        <div className="card max-w-[560px]">
          <div className="font-[var(--display)] font-semibold text-[17px] mb-2">
            post not found
          </div>
          <p className="text-[14px]" style={{ color: "var(--muted)" }}>
            it may have been removed. <Link href="/feed" style={{ color: "var(--yellow)" }}>back to posts →</Link>
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="card max-w-[560px]">
          <p className="text-[14px]" style={{ color: "var(--bad)" }}>
            {error}
          </p>
        </div>
      )}

      {!loading && post && (
        <>
          <div className={styles.head}>
            <h1 className={styles.title}>{titleOf(post)}</h1>
            <div className={styles.meta}>
              {timeAgo(post.created_at)} · {post.status}
            </div>
          </div>

          <div className={styles.grid}>
            <div className={styles.postcard}>
              <div className={styles.body}>{post.body}</div>

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
            </div>

            <EvalPanel score={post.score} />
          </div>
        </>
      )}
    </div>
  );
}
