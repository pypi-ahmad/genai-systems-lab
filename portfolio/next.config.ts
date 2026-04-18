import path from "node:path";
import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const rawApiBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim();
if (isProd && !rawApiBase) {
  // Fail the build instead of silently baking in a localhost fallback that
  // would ship to production and make every API call CORS-error.
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL must be set when building the portfolio for production.",
  );
}
const apiBaseForCsp = rawApiBase || "http://localhost:8000";

/**
 * Content Security Policy.
 *
 * Next.js App Router with React 19 requires inline ``style-src`` for its
 * server-rendered CSS injection and ``script-src 'self'`` with
 * ``'strict-dynamic'``-style nonces for hydration.  We keep this policy
 * conservative (no ``unsafe-eval``, no third-party script origins) while
 * tolerating Next's own inline styles.
 */
function buildCsp(): string {
  const connectSrc = ["'self'", apiBaseForCsp].filter(Boolean).join(" ");
  return [
    "default-src 'self'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    // Tailwind v4 + Next.js still need inline styles during hydration.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    // ``'unsafe-inline'`` is required for Next's bootstrap scripts in prod;
    // tighten to nonces if you adopt a custom server.
    `script-src 'self'${isProd ? " 'unsafe-inline'" : " 'unsafe-inline' 'unsafe-eval'"}`,
    `connect-src ${connectSrc}`,
    "object-src 'none'",
    "manifest-src 'self'",
    "worker-src 'self' blob:",
  ].join("; ");
}

const securityHeaders = [
  { key: "Content-Security-Policy", value: buildCsp() },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "no-referrer" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=()",
  },
  ...(isProd
    ? [
        {
          key: "Strict-Transport-Security",
          value: "max-age=63072000; includeSubDomains",
        },
      ]
    : []),
];

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.resolve(process.cwd(), ".."),
  turbopack: {
    root: path.resolve(process.cwd(), ".."),
  },
  // React 19 + Next 16 sane defaults.
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
