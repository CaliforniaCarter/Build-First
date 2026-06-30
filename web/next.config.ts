import type { NextConfig } from "next";

// /api/* is proxied to the FastAPI backend by app/api/[...path]/route.ts (a route
// handler, not a rewrite — rewrites abort long upstream calls ~30s, and compose can
// take ~45s). Same-origin from the browser's view, so no CORS.
const nextConfig: NextConfig = {
  // Next 16 blocks cross-origin dev requests by default; allow local hosts so the
  // browser (which may reach the dev server as 127.0.0.1) can load HMR.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
