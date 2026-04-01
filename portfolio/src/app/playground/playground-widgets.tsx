"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { TimelineReplayFrame } from "@/components/TimelineReplay";
import { workspaceStateLabel, workspaceStateTone, type WorkspaceState } from "./playground-utils";

/* ── Spinner ──────────────────────────────────────────── */

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z" />
    </svg>
  );
}

export function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 align-middle text-current">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-current"
          style={{ animation: `blink 900ms ${i * 120}ms infinite` }}
        />
      ))}
    </span>
  );
}

const thinkingStates = ["Thinking", "Analyzing", "Planning steps"] as const;

export function ThinkingStateList() {
  return (
    <div className="mt-4 space-y-2.5">
      {thinkingStates.map((state, index) => (
        <div
          key={state}
          className="flex items-center gap-2 text-sm leading-7 text-[var(--muted)] transition-opacity duration-300 ease-in-out"
          style={{ animation: `thinkPulse 1800ms ease-in-out ${index * 180}ms infinite` }}
        >
          <span>{state}</span>
          <TypingDots />
        </div>
      ))}
    </div>
  );
}

/* ── Debug Panel ─────────────────────────────────────── */

export function DebugPanel({
  logs,
  title = "Debug Panel",
  subtitle = "Live execution log",
  onClear,
}: {
  logs: string[];
  title?: string;
  subtitle?: string;
  onClear?: () => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (copyState === "idle") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyState("idle");
    }, 1600);

    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  const copyLogs = useCallback(async () => {
    if (logs.length === 0) {
      return;
    }

    try {
      await navigator.clipboard.writeText(logs.join("\n"));
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }, [logs]);

  return (
    <section className="overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#0B0F14] shadow-[0_22px_48px_-28px_rgba(2,6,23,0.72)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-4 py-3 sm:px-5">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
            {title}
          </p>
          <p className="mt-1 text-sm font-semibold text-white/82">
            {subtitle}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/45">
            {logs.length} lines
          </span>
          {copyState === "copied" && (
            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300">
              Copied
            </span>
          )}
          {copyState === "error" && (
            <span className="rounded-full border border-rose-400/20 bg-rose-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-rose-300">
              Copy failed
            </span>
          )}
          <button
            type="button"
            onClick={() => void copyLogs()}
            disabled={logs.length === 0}
            className="button-base button-sm button-pill border border-white/10 bg-white/5 text-white/72 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-35"
          >
            Copy
          </button>
          {onClear ? (
            <button
              type="button"
              onClick={onClear}
              disabled={logs.length === 0}
              className="button-base button-sm button-pill border border-white/10 bg-transparent text-white/58 hover:bg-white/8 hover:text-white disabled:cursor-not-allowed disabled:opacity-35"
            >
              Clear logs
            </button>
          ) : null}
        </div>
      </div>

      <div
        ref={scrollRef}
        className="max-h-[360px] overflow-y-auto px-5 py-5 font-mono text-[11px] leading-6 text-[#86EFAC] sm:px-6"
      >
        {logs.length > 0 ? (
          <div className="space-y-0.5">
            {logs.map((line, index) => (
              <div key={`${index}-${line}`} className="whitespace-pre-wrap break-words">
                {line}
              </div>
            ))}
          </div>
        ) : (
          <div className="whitespace-pre-wrap text-white/35">
            Waiting for execution logs.
          </div>
        )}
      </div>
    </section>
  );
}

/* ── Stat Card ───────────────────────────────────────── */

export function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="surface-panel rounded-[1.25rem] px-5 py-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-2 text-base font-semibold text-[var(--foreground)]">
        {value}
      </p>
    </div>
  );
}

/* ── Workspace / Replay badges ───────────────────────── */

export function WorkspaceStateBadge({ state }: { state: WorkspaceState }) {
  if (state === "thinking") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <Spinner className="h-3 w-3" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "streaming") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <Spinner className="h-3 w-3" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "completed") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--success-dot)]" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  if (state === "error") {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--error-dot)]" />
        {workspaceStateLabel(state)}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${workspaceStateTone(state)}`}>
      {workspaceStateLabel(state)}
    </span>
  );
}

export function ReplayStateBadge({
  frame,
  totalEvents,
}: {
  frame: TimelineReplayFrame | null;
  totalEvents: number;
}) {
  const replayFinished = totalEvents > 0 && (frame?.currentIndex ?? -1) >= totalEvents - 1;
  const isPlaying = Boolean(frame?.isPlaying) && !replayFinished;
  const tone = replayFinished
    ? "border-[var(--done-border)] bg-[var(--done-bg)] text-[var(--done-text)]"
    : isPlaying
      ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft-strong)] text-[color-mix(in_srgb,var(--accent-solid)_72%,var(--text)_28%)]"
      : "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]";
  const label = replayFinished ? "Replay complete" : isPlaying ? "Replay playing" : "Replay paused";

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}>
      {label}
    </span>
  );
}
