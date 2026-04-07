"use client";

import { useEffect, useState } from "react";
import { fetchMetrics, type ProjectMetrics } from "@/lib/api";

let metricsCache: Map<string, ProjectMetrics> | null = null;
let fetchPromise: Promise<void> | null = null;

function loadMetrics(): Promise<void> {
  if (metricsCache) return Promise.resolve();
  if (fetchPromise) return fetchPromise;
  fetchPromise = fetchMetrics()
    .then((res) => {
      metricsCache = new Map(res.projects.map((p) => [p.name, p]));
    })
    .catch(() => {
      metricsCache = new Map();
    });
  return fetchPromise;
}

export function ProjectRunBadge({ slug }: { slug: string }) {
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    void loadMetrics().then(() => {
      setMetrics(metricsCache?.get(slug) ?? null);
      setLoaded(true);
    });
  }, [slug]);

  if (!loaded || !metrics) return null;

  const successPct = Math.round(metrics.success_rate * 100);

  return (
    <span className="text-[11px] text-[var(--muted)]">
      {successPct}% success · {metrics.latency.toFixed(1)}s avg
    </span>
  );
}
