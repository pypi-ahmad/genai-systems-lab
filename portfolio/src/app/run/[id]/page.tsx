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
  const [inputOpen, setInputOpen] = useState(false);

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
    { key: "memory" as const, label: `Reasoning (${run.memory.length})` },
    { key: "timeline" as const, label: `Execution log (${run.timeline.length})` },
  ];

  return (
    <section className="py-16">
      <div className="surface-card rounded-[1.75rem] p-6 sm:p-8">
        {/* Context banner */}
        <div className="rounded-[1rem] border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-4 py-3">
          <p className="text-sm leading-6 text-[var(--foreground)]">
            You&apos;re viewing a saved run of <span className="font-semibold">{proj?.name ?? run.project}</span>.
            {proj?.description ? ` ${proj.description}` : ""}
          </p>
          <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">
            The output below is exactly what the model produced. Want to try it yourself? Open the playground, bring your own API key, and run any of the 20 systems live.
          </p>
        </div>

        {/* Header */}
        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{proj?.category ?? "Project"}</p>
            <h1 className="mt-1 text-2xl font-bold text-[var(--foreground)]">{proj?.name ?? run.project}</h1>
            <p className="mt-1 text-xs text-[var(--muted)]">{formatTimestamp(run.timestamp)}</p>
          </div>
          <div className="flex w-full max-w-[240px] flex-col gap-3 sm:items-end">
            <ConfidenceIndicator confidence={run.confidence} />
            <Link href="/playground" className="button-base button-primary button-sm button-pill sm:self-end">
              Try it yourself
            </Link>
          </div>
        </div>

        {/* Summary stats */}
        <div className="mt-5 flex flex-wrap gap-3">
          <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">
            Response time: {run.latency.toFixed(0)} ms
          </span>
          <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">
            Confidence: {(run.confidence * 100).toFixed(0)}%
          </span>
          {run.memory.length > 0 && (
            <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">
              {run.memory.length} reasoning {run.memory.length === 1 ? "step" : "steps"}
            </span>
          )}
          {run.timeline.length > 0 && (
            <span className="surface-pill rounded-full px-3 py-1 text-[11px] font-semibold text-[var(--muted)]">
              {run.timeline.length} execution {run.timeline.length === 1 ? "event" : "events"}
            </span>
          )}
        </div>

        {/* Input (collapsed by default) */}
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setInputOpen((v) => !v)}
            className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)] transition-colors hover:text-[var(--foreground)]"
          >
            <span>Input sent to the model</span>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={`h-4 w-4 transition-transform duration-200 ${inputOpen ? "rotate-180" : ""}`}>
              <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
            </svg>
          </button>
          {inputOpen && (
            <div className="surface-panel mt-2 rounded-[1rem] p-4">
              <p className="font-mono text-sm leading-7 text-[var(--foreground)] whitespace-pre-wrap">{run.input}</p>
            </div>
          )}
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
          {activeTab === "memory" && run.memory.length > 0 && (
            <p className="mb-3 text-[11px] leading-5 text-[var(--muted)]">
              Each entry below is one step in the model&apos;s reasoning.
              <span className="font-semibold text-[var(--info-text)]"> Thoughts</span> are internal planning,
              <span className="font-semibold text-[var(--warning-text)]"> actions</span> are tool calls or decisions, and
              <span className="font-semibold text-[var(--success-text)]"> observations</span> are results the model received back.
            </p>
          )}
          {activeTab === "timeline" && run.timeline.length > 0 && (
            <p className="mb-3 text-[11px] leading-5 text-[var(--muted)]">
              Each row is one execution event, shown in order with the time elapsed since the run started.
            </p>
          )}
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
