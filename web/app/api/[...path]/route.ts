// Proxy /api/* to the FastAPI backend. Replaces next.config rewrites, which abort
// long upstream calls (~30s) — compose runs many sequential LLM calls and can take
// ~45s. A route handler awaits the full upstream response with no such cap.

const API_TARGET = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

async function handler(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const search = new URL(req.url).search;
  const target = `${API_TARGET}/api/${path.join("/")}${search}`;

  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers: { "content-type": req.headers.get("content-type") ?? "application/json" },
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  try {
    const res = await fetch(target, init);
    const body = await res.text();
    return new Response(body, {
      status: res.status,
      headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ detail: `proxy error: ${(err as Error).message}` }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }
}

export {
  handler as GET,
  handler as POST,
  handler as PUT,
  handler as PATCH,
  handler as DELETE,
};
