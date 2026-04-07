"use client";

import { useState } from "react";

export type MemoryEntryType = "thought" | "action" | "observation";

export type MemoryEntry = {
  id: string;
  stepName: string;
  type: MemoryEntryType;
  content: string;
  timestamp?: string;
  initiallyExpanded?: boolean;
};

type MemoryPanelProps = {
  entries: MemoryEntry[];
  title?: string;
  description?: string;
  emptyState?: string;
  className?: string;
};

function joinClasses(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function entryTypeLabel(type: MemoryEntryType) {
  if (type === "thought") return "Reasoning";
  if (type === "action") return "Action Taken";
  return "Result Received";
}

function entryBadgeTone(type: MemoryEntryType) {
  if (type === "thought") {
    return "border-[var(--accent-border-soft)] bg-[var(--accent-soft)] text-[var(--accent-solid)]";
  }

  if (type === "action") {
    return "border-[var(--running-border)] bg-[var(--running-bg)] text-[var(--running-text)]";
  }

  return "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]";
}

function entryIconTone(type: MemoryEntryType) {
  if (type === "thought") {
    return "border-[var(--accent-border-soft)] bg-[var(--accent-soft)] text-[var(--accent-solid)]";
  }

  if (type === "action") {
    return "border-[var(--running-border)] bg-[var(--running-bg)] text-[var(--running-text)]";
  }

  return "border-[var(--line)] bg-[var(--panel)] text-[var(--muted)]";
}

function EntryIcon({ type }: { type: MemoryEntryType }) {
  if (type === "thought") {
    return (
      <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
        <path d="M10 3.5 11.5 7l3.5 1.5-3.5 1.5L10 13.5 8.5 10 5 8.5 8.5 7 10 3.5Z" fill="currentColor" />
      </svg>
    );
  }

  if (type === "action") {
    return (
      <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
        <path d="M5 10h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <path d="m10 6 4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
      <path d="M2.5 10c1.8-3 4.3-4.5 7.5-4.5S15.7 7 17.5 10c-1.8 3-4.3 4.5-7.5 4.5S4.3 13 2.5 10Z" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="10" cy="10" r="2.2" fill="currentColor" />
    </svg>
  );
}

export function MemoryPanel({
  entries,
  title = "Agent Memory",
  description = "Timeline of the agent's thoughts, actions, and observations.",
  emptyState = "Memory entries will appear here as the run progresses.",
  className,
}: MemoryPanelProps) {
  const [expandedEntries, setExpandedEntries] = useState<Record<string, boolean>>({});

  return (
    <section
      className={joinClasses(
        "rounded-[1rem] border border-[var(--line)] bg-[var(--card)] p-4 transition-all duration-300 ease-in-out",
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            {title}
            <span
              title="Shows the agent's internal reasoning, tool calls, and observations during execution"
              className="cursor-help text-xs normal-case tracking-normal hover:text-[var(--foreground)]"
              aria-label="Shows the agent's internal reasoning, tool calls, and observations during execution"
            >
              ⓘ
            </span>
          </p>
          <p className="mt-1 text-sm leading-7 text-[var(--muted)]">
            {description}
          </p>
        </div>
        <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
          {entries.length} entries
        </span>
      </div>

      {entries.length === 0 ? (
        <div className="mt-4 rounded-[1rem] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] px-4 py-6 text-sm leading-7 text-[var(--muted)]">
          {emptyState}
        </div>
      ) : (
        <div className="relative mt-5 space-y-4 before:absolute before:bottom-0 before:left-[15px] before:top-1 before:w-px before:bg-[var(--line)]">
          {entries.map((entry, index) => {
            const isExpanded = expandedEntries[entry.id] ?? entry.initiallyExpanded ?? index === entries.length - 1;

            return (
              <article key={entry.id} className="relative pl-11">
                <span
                  className={joinClasses(
                    "absolute left-0 top-1 flex h-8 w-8 items-center justify-center rounded-full border shadow-sm transition-colors duration-300",
                    entryIconTone(entry.type),
                  )}
                >
                  <EntryIcon type={entry.type} />
                </span>

                <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-3 transition-all duration-300 ease-in-out">
                  <button
                    type="button"
                    onClick={() => {
                      setExpandedEntries((previous) => ({
                        ...previous,
                        [entry.id]: !isExpanded,
                      }));
                    }}
                    aria-expanded={isExpanded}
                    className="flex w-full items-start justify-between gap-3 text-left"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-[var(--foreground)]">
                          {entry.stepName}
                        </p>
                        <span
                          className={joinClasses(
                            "rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]",
                            entryBadgeTone(entry.type),
                          )}
                        >
                          {entryTypeLabel(entry.type)}
                        </span>
                        {entry.timestamp && (
                          <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-[var(--muted)]">
                            {entry.timestamp}
                          </span>
                        )}
                      </div>

                      {!isExpanded && (
                        <p className="mt-2 line-clamp-2 text-sm leading-7 text-[var(--muted)]">
                          {entry.content}
                        </p>
                      )}
                    </div>

                    <span className="surface-pill rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                      {isExpanded ? "Collapse" : "Expand"}
                    </span>
                  </button>

                  <div
                    className={joinClasses(
                      "grid transition-all duration-300 ease-in-out",
                      isExpanded ? "grid-rows-[1fr] opacity-100 pt-3" : "grid-rows-[0fr] opacity-0",
                    )}
                  >
                    <div className="overflow-hidden">
                      <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--foreground)]">
                        {entry.content}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}