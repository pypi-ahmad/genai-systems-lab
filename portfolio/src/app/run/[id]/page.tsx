"use client";

import Link from "next/link";
import { useEffect, useState, use } from "react";
import { fetchSharedRun, type SharedRun, type RunMemoryEntry, type RunTimelineEntry } from "@/lib/api";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { projectDetails } from "@/data/projects";

function Spinner({ className }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className ?? "h-5 w-5"}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function formatTimestamp(ts: string | null) {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

function MemoryItem({ entry }: { entry: RunMemoryEntry }) {
  const typeColors: Record<string, string> = {
    thought: "text-[var(--info-text)] bg-[var(--info-bg)]",
    action: "text-[var(--warning-text)] bg-[var(--warning-bg)]",
    observation: "text-[var(--success-text)] bg-[var(--success-bg)]",
  };

  return (
    <div className="surface-panel rounded-[0.75rem] p-3">
      <div className="flex items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${typeColors[entry.type] ?? "text-[var(--muted)] bg-[var(--surface-soft)]"}`}>
          {entry.type}
        </span>
        <span className="text-xs font-semibold text-[var(--foreground)]">{entry.step}</span>
      </div>
      <p className="mt-2 font-mono text-xs leading-6 text-[var(--muted)]">{entry.content}</p>
    </div>
  );
}

function TimelineItem({ entry }: { entry: RunTimelineEntry }) {
  return (
    <div className="flex items-start gap-3 surface-panel rounded-[0.75rem] p-3">
      <span className="shrink-0 rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-semibold tabular-nums text-[var(--accent)]">
        {entry.timestamp.toFixed(2)}s
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold text-[var(--foreground)]">
          {entry.step} <span className="font-normal text-[var(--muted)]">· {entry.event}</span>
        </p>
        {entry.data && (
          <p className="mt-1 line-clamp-3 font-mono text-[11px] leading-5 text-[var(--muted)]">{entry.data}</p>
        )}
      </div>
    </div>
  );
}

export default function SharedRunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: shareToken } = use(params);
  const [run, setRun] = useState<SharedRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"output" | "memory" | "timeline">("output");

  useEffect(() => {
    fetchSharedRun(shareToken)
      .then(setRun)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load shared run.");
      })
      .finally(() => setLoading(false));
  }, [shareToken]);

  if (loading) {
    return (
      <section className="py-16">
        <div className="surface-card flex items-center justify-center gap-3 rounded-[1.75rem] p-12">
          <Spinner className="h-5 w-5 text-[var(--accent)]" />
          <span className="text-sm text-[var(--muted)]">Loading shared run…</span>
        </div>
      </section>
    );
  }

  if (error || !run) {
    return (
      <section className="py-16">
        <div className="surface-card rounded-[1.75rem] p-8 text-center">
          <p className="text-lg font-semibold text-[var(--danger-text)]">
            {error?.includes("410") ? "This shared link has expired." : error?.includes("404") ? "Shared run not found." : error ?? "Something went wrong."}
          </p>
          <Link href="/playground" className="mt-4 inline-block button-base button-primary button-sm button-pill">
            Go to Playground
          </Link>
        </div>
      </section>
    );
  }

  const proj = projectDetails.find((p) => p.slug === run.project);

  const tabs = [
    { key: "output" as const, label: "Output" },
    { key: "memory" as const, label: `Memory (${run.memory.length})` },
    { key: "timeline" as const, label: `Timeline (${run.timeline.length})` },
  ];

  return (
    <section className="py-16">
      <div className="surface-card rounded-[1.75rem] p-6 sm:p-8">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Shared Run</p>
            <h1 className="mt-1 text-2xl font-bold text-[var(--foreground)]">{proj?.name ?? run.project}</h1>
            <p className="mt-1 text-xs text-[var(--muted)]">{formatTimestamp(run.timestamp)} · {run.latency.toFixed(0)} ms</p>
          </div>
          <div className="flex w-full max-w-[240px] flex-col gap-3 sm:items-end">
            <ConfidenceIndicator confidence={run.confidence} />
            <Link href="/playground" className="button-base button-secondary button-sm button-pill sm:self-end">
              Open Playground
            </Link>
          </div>
        </div>

        {/* Input */}
        <div className="mt-6">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Input</p>
          <div className="surface-panel mt-2 rounded-[1rem] p-4">
            <p className="font-mono text-sm leading-7 text-[var(--foreground)] whitespace-pre-wrap">{run.input}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6 flex gap-1 border-b border-[var(--line)]">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors ${
                activeTab === tab.key
                  ? "border-b-2 border-[var(--accent)] text-[var(--accent)]"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="mt-4">
          {activeTab === "output" && (
            <div className="surface-panel rounded-[1rem] p-4">
              <p className="font-mono text-sm leading-7 text-[var(--foreground)] whitespace-pre-wrap">{run.output}</p>
            </div>
          )}

          {activeTab === "memory" && (
            <div className="space-y-2">
              {run.memory.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">No memory entries for this run.</p>
              ) : (
                run.memory.map((entry, i) => <MemoryItem key={i} entry={entry} />)
              )}
            </div>
          )}

          {activeTab === "timeline" && (
            <div className="space-y-2">
              {run.timeline.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">No timeline events for this run.</p>
              ) : (
                run.timeline.map((entry, i) => <TimelineItem key={i} entry={entry} />)
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
