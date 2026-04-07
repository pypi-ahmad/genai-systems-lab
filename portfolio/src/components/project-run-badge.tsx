"use client";

import { useEffect, useState } from "react";
import { fetchMetricsTime } from "@/lib/api";

type AggregateStats = {
  runs: number;
  successRate: number;
};

let cachedStats: AggregateStats | null | undefined;

/**
 * Shows aggregate run stats from the metrics API.
 * Falls back to nothing if metrics are unavailable.
 */
export function AggregateRunBadge() {
  const [stats, setStats] = useState<AggregateStats | null | undefined>(cachedStats);

  useEffect(() => {
    if (cachedStats !== undefined) return;
    cachedStats = null; // mark as loading

    let cancelled = false;
    void (async () => {
      try {
        const data = await fetchMetricsTime({ range: "week" });
        if (data.length === 0) {
          if (!cancelled) { cachedStats = null; setStats(null); }
          return;
        }
        const success = data.filter((p) => p.success).length;
        const total = data.length;
        const result: AggregateStats = {
          runs: total,
          successRate: Math.round((success / total) * 100),
        };
        if (!cancelled) { cachedStats = result; setStats(result); }
      } catch {
        if (!cancelled) { cachedStats = null; setStats(null); }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (!stats || stats.runs === 0) return null;

  return (
    <span className="surface-pill rounded-full px-3 py-1 text-xs text-[var(--muted)]">
      {stats.runs} runs this week · {stats.successRate}% success
    </span>
  );
}
