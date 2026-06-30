// Thin client for the FastAPI backend. Every call maps to one engine-backed endpoint.
import type { Intake } from "./intake";

// Same-origin by default: calls go to /api/* and Next rewrites them to the backend
// (see next.config.ts). Set NEXT_PUBLIC_API_BASE to hit the API directly instead.
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// ── score / post shapes the API returns (serialize_score + PostRecord) ──────
export interface ScoreGate {
  name: string;
  passed: boolean;
  reason: string;
}
export interface ScoreDim {
  name: string;
  score: number;
  reason: string;
}
export interface SerializedScore {
  gates: ScoreGate[];
  dimensions: ScoreDim[];
  delta_vs_prev: string;
  quality_avg: number;
  gates_passed: number;
  gates_total: number;
  passes_threshold: boolean;
  headline: string;
}
export interface PostRecord {
  id: string;
  body: string;
  score: SerializedScore;
  proof: string[];
  redactions: string[];
  council_log: { pass: number; critique: string; reason: string; stop: boolean }[];
  status: "draft" | "approved";
  topic: string;
  created_at: string;
  updated_at: string;
}
export interface Insight {
  observation: string;
  verbatim_quote: string;
  trait_label: string;
}
export interface ScanProfile {
  handle: string;
  post_count: number;
  posts: { text: string; url?: string; posted_at?: string }[];
}

export const api = {
  getIntake: () => req<Intake>("/api/intake"),
  putIntake: (intake: Intake) =>
    req<{ ok: boolean; intake: Intake }>("/api/intake", {
      method: "PUT",
      body: JSON.stringify(intake),
    }),
  patchIntake: (patch: Record<string, unknown>) =>
    req<{ ok: boolean; intake: Intake }>("/api/intake", {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  scan: (linkedin: string, x: string) =>
    req<{ linkedin: ScanProfile; x: ScanProfile; pending: boolean }>("/api/online/scan", {
      method: "POST",
      body: JSON.stringify({ linkedin, x }),
    }),

  buildProfile: () =>
    req<{ profile_md: string; context_md: string }>("/api/profile/build", { method: "POST" }),
  getDocs: () =>
    req<{ persona_md: string; profile_md: string; context_md: string }>("/api/profile/docs"),
  putPersonaDoc: (persona_md: string) =>
    req<{ ok: boolean }>("/api/profile/docs", {
      method: "PUT",
      body: JSON.stringify({ persona_md }),
    }),

  buildPersona: () => req<{ persona_md: string }>("/api/persona/build", { method: "POST" }),
  personaInsights: () =>
    req<{ insights: Insight[] }>("/api/persona/insights", { method: "POST" }),

  compose: (work: string, save = true) =>
    req<{ post: PostRecord }>("/api/compose", {
      method: "POST",
      body: JSON.stringify({ work, save }),
    }),

  listPosts: (status?: "draft" | "approved") =>
    req<{ posts: PostRecord[] }>(`/api/posts${status ? `?status=${status}` : ""}`),
  getPost: (id: string) => req<PostRecord>(`/api/posts/${id}`),
  approvePost: (id: string) => req<PostRecord>(`/api/posts/${id}/approve`, { method: "POST" }),
  patchPost: (id: string, body: { body?: string; rescore?: boolean }) =>
    req<PostRecord>(`/api/posts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
};
