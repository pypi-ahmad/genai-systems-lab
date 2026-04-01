"use client";

import { useEffect, useState } from "react";

import { fetchLeaderboard, getApiUrl, type LeaderboardEntry } from "@/lib/api";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";

function formatProject(project: string) {
  return project.replace(/^(genai-|crew-|lg-)/, "").replace(/-/g, " ");
}

function formatAccuracy(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatLatency(value: number) {
  return `${value.toFixed(2)} ms`;
}

function formatScore(value: number) {
  return value.toFixed(4);
}

function EmptyState({ message }: { message: string }) {
  return (
    <section className="py-16">
      <div className="surface-card rounded-xl p-6 sm:p-8">
        <p className="eyebrow">Benchmarks</p>
        <h2 className="heading-section mt-3 text-3xl text-[var(--foreground)]">
          No benchmark results available
        </h2>
        <p className="copy-body mt-4 max-w-2xl text-sm">{message}</p>
      </div>
    </section>
  );
}

export default function LeaderboardPage() {
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const normalizedApiKey = apiKey.trim();
    if (!normalizedApiKey) {
      setEntries([]);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    fetchLeaderboard(normalizedApiKey)
      .then((response) => {
        setEntries(response);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load leaderboard.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [apiKey]);

  function handleApiKeyChange(nextApiKey: string) {
    setApiKey(nextApiKey);
    setStoredApiKey(nextApiKey.trim());
  }

  if (!apiKey.trim()) {
    return (
      <section className="space-y-8 py-16">
        <div className="title-stack">
          <p className="eyebrow">Benchmark Leaderboard</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Compare projects with your own Gemini API key.
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            This ranking runs live benchmark suites. Enter your Google API key to generate a real leaderboard.
          </p>
        </div>

        <div className="surface-card rounded-xl p-6 sm:p-8">
          <label className="block">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Google API Key
            </span>
            <input
              type="password"
              value={apiKey}
              onChange={(event) => handleApiKeyChange(event.target.value)}
              autoComplete="off"
              spellCheck={false}
              placeholder="AIza..."
              className="input-shell mt-3 w-full rounded-[1rem] px-4 py-3 font-mono text-xs leading-6"
            />
          </label>
          <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
            The leaderboard now requires BYOK because benchmark runs execute live against the backend.
          </p>
          <p className="mt-4 font-mono text-sm text-[var(--muted)]">GET {getApiUrl("/leaderboard")}</p>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="flex min-h-[50vh] items-center justify-center py-16">
        <div className="surface-card flex items-center gap-3 rounded-full px-5 py-3 text-sm text-[var(--muted)]">
          <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
          Loading leaderboard.
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="space-y-8 py-16">
        <div className="title-stack">
          <p className="eyebrow">Leaderboard</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Benchmark ranking across all projects.
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            Live benchmark runs require your Google API key.
          </p>
        </div>

        <div className="surface-card error-panel rounded-xl p-6 sm:p-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--danger-text)]">
            Unable to load leaderboard
          </p>
          <p className="mt-4 text-base leading-8 text-[var(--danger-text-soft)]">{error}</p>
          <p className="mt-4 font-mono text-sm text-[var(--danger-text)]">GET {getApiUrl("/leaderboard")}</p>
        </div>
      </section>
    );
  }

  if (entries.length === 0) {
    return <EmptyState message="Register benchmark datasets and expose the API to populate this ranking." />;
  }

  const bestProject = entries[0];

  return (
    <div className="space-y-0">
      <section className="grid gap-8 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="title-stack">
          <p className="eyebrow">Benchmark Leaderboard</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Rank projects by benchmark accuracy per millisecond.
          </h1>
          <p className="copy-lead max-w-2xl text-lg">
            Each score uses the requested formula: accuracy divided by mean latency. Higher is better. Runs execute live with your BYOK Gemini key.
          </p>
        </div>

        <div className="space-y-4">
          <div className="surface-panel rounded-xl px-4 py-4 text-sm leading-7 text-[var(--muted)]">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Active benchmark key
            </p>
            <p className="mt-2 font-mono text-xs text-[var(--foreground)]">{`${apiKey.slice(0, 4)}${"•".repeat(Math.max(0, Math.min(apiKey.length - 7, 20)))}${apiKey.slice(-3)}`}</p>
          </div>
          <div className="surface-card rounded-xl border-[var(--accent-border-soft)] bg-[var(--accent-soft)] p-6 sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Best Project
            </p>
            <p className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-[var(--foreground)] capitalize">
              {formatProject(bestProject.project)}
            </p>
            <div className="mt-4 grid gap-6 sm:grid-cols-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Accuracy</p>
                <p className="mt-1 text-sm font-semibold">{formatAccuracy(bestProject.accuracy)}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Latency</p>
                <p className="mt-1 text-sm font-semibold">{formatLatency(bestProject.latency)}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Score</p>
                <p className="mt-1 text-sm font-semibold">{formatScore(bestProject.score)}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="surface-card overflow-hidden rounded-xl">
          <div className="border-b border-[var(--line)] bg-[var(--surface-soft)] px-6 py-5 sm:px-8">
            <p className="eyebrow">Ranking Table</p>
            <h2 className="heading-section mt-2 text-3xl text-[var(--foreground)]">
              Accuracy, latency, and composite score.
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--line)] bg-[var(--surface-soft)]">
                  <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] sm:px-8">Rank</th>
                  <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] sm:px-8">Project</th>
                  <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] sm:px-8">Accuracy</th>
                  <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] sm:px-8">Latency</th>
                  <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] sm:px-8">Score</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, index) => {
                  const isBest = index === 0;

                  return (
                    <tr
                      key={entry.project}
                      className={isBest ? "bg-[var(--accent-soft)]" : "border-t border-[var(--line)]/70"}
                    >
                      <td className="px-6 py-5 sm:px-8">
                        <span className={`inline-flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold ${isBest ? "button-primary text-[var(--accent-contrast)]" : "surface-pill text-[var(--foreground)]"}`}>
                          {index + 1}
                        </span>
                      </td>
                      <td className="px-6 py-5 sm:px-8">
                        <div className="flex items-center gap-3">
                          <div>
                            <p className="font-semibold capitalize text-[var(--foreground)]">
                              {formatProject(entry.project)}
                            </p>
                            <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.12em] text-[var(--muted)]">
                              {entry.project}
                            </p>
                          </div>
                          {isBest && (
                            <span className="rounded-full bg-[var(--foreground)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--bg)]">
                              Best
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-5 font-semibold text-[var(--foreground)] sm:px-8">{formatAccuracy(entry.accuracy)}</td>
                      <td className="px-6 py-5 font-semibold text-[var(--foreground)] sm:px-8">{formatLatency(entry.latency)}</td>
                      <td className="px-6 py-5 sm:px-8">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${isBest ? "status-positive" : "surface-pill text-[var(--foreground)]"}`}>
                          {formatScore(entry.score)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}