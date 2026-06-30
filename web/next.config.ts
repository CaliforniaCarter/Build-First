import type { NextConfig } from "next";

// Proxy /api/* to the FastAPI backend so the browser only ever talks to its own
// origin (no CORS, and it works when the page host can't reach :8000 directly).
// Override the target with API_PROXY_TARGET if the backend runs elsewhere.
const API_TARGET = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Next 16 blocks cross-origin dev requests by default; allow local hosts so the
  // browser (which may reach the dev server as 127.0.0.1) can load HMR + call /api.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_TARGET}/api/:path*` }];
  },
};

export default nextConfig;
