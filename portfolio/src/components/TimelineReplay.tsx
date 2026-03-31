"use client";

import { useEffect, useRef, useState } from "react";

export type TimelineReplayEntry = {
  timestamp: number;
  step: string;
  event: string;
  data: string;
};

export type TimelineReplayFrame = {
  currentIndex: number;
  currentEntry: TimelineReplayEntry | null;
  playedEntries: TimelineReplayEntry[];
  progress: number;
  isPlaying: boolean;
  speed: number;
};

type TimelineReplayProps = {
  entries: TimelineReplayEntry[];
  title?: string;
  description?: string;
  emptyState?: string;
  sourceLabel?: string;
  autoplayKey?: string | number;
  formatStepLabel?: (step: string) => string;
  onFrameChange?: (frame: TimelineReplayFrame) => void;
  onClose?: () => void;
};

type TimelineReplayInnerProps = TimelineReplayProps;

const SPEED_OPTIONS = [0.5, 1, 1.5, 2, 4] as const;

function joinClasses(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function formatEventLabel(event: string) {
  if (event === "running") return "Running";
  if (event === "done") return "Completed";
  if (event === "error") return "Failed";
  if (event === "completed") return "Run Complete";
  if (event === "failed") return "Run Failed";
  return event.replace(/[_-]+/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatReplayTime(timestamp: number) {
  if (!Number.isFinite(timestamp)) {
    return "+0.00s";
  }

  return `+${timestamp.toFixed(timestamp >= 10 ? 1 : 2)}s`;
}

function markerPosition(index: number, total: number) {
  if (total <= 1) {
    return 0;
  }

  return (index / (total - 1)) * 100;
}

function progressValue(currentIndex: number, total: number) {
  if (currentIndex < 0 || total === 0) {
    return 0;
  }

  if (total === 1) {
    return 1;
  }

  return currentIndex / (total - 1);
}

function playbackDelay(current: TimelineReplayEntry, next: TimelineReplayEntry, speed: number) {
  const deltaMs = (next.timestamp - current.timestamp) * 1000;
  if (!Number.isFinite(deltaMs) || deltaMs <= 0) {
    return 280;
  }

  return Math.max(180, Math.min(1600, deltaMs / speed));
}

function TimelineReplayInner({
  entries,
  title = "Timeline Replay",
  description = "Play back saved execution events in sequence.",
  emptyState = "Replay data will appear here after a run with timeline capture is saved.",
  sourceLabel,
  formatStepLabel,
  onFrameChange,
  onClose,
}: TimelineReplayInnerProps) {
  const [currentIndex, setCurrentIndex] = useState(entries.length > 0 ? 0 : -1);
  const [isPlaying, setIsPlaying] = useState(entries.length > 1);
  const [speed, setSpeed] = useState<(typeof SPEED_OPTIONS)[number]>(1);
  const timeoutRef = useRef<number | null>(null);

  const resolvedFormatStepLabel = formatStepLabel ?? ((step: string) => step);
  const currentEntry = currentIndex >= 0 ? entries[currentIndex] ?? null : null;
  const playedEntries = currentIndex >= 0 ? entries.slice(0, currentIndex + 1) : [];
  const progress = progressValue(currentIndex, entries.length);

  const stepLabels: Array<{ step: string; label: string }> = [];
  for (const entry of entries) {
    if (!stepLabels.some((item) => item.step === entry.step)) {
      stepLabels.push({ step: entry.step, label: resolvedFormatStepLabel(entry.step) });
    }
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    onFrameChange?.({
      currentIndex,
      currentEntry: currentIndex >= 0 ? entries[currentIndex] ?? null : null,
      playedEntries: currentIndex >= 0 ? entries.slice(0, currentIndex + 1) : [],
      progress,
      isPlaying,
      speed,
    });
  }, [currentIndex, entries, isPlaying, onFrameChange, progress, speed]);

  useEffect(() => {
    if (!isPlaying || currentIndex < 0 || currentIndex >= entries.length - 1) {
      return undefined;
    }

    const delay = playbackDelay(entries[currentIndex], entries[currentIndex + 1], speed);
    timeoutRef.current = window.setTimeout(() => {
      const nextIndex = Math.min(entries.length - 1, currentIndex + 1);
      setCurrentIndex(nextIndex);
      if (nextIndex >= entries.length - 1) {
        setIsPlaying(false);
      }
    }, delay);

    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [currentIndex, entries, isPlaying, speed]);

  const replayFinished = entries.length > 0 && currentIndex >= entries.length - 1;
  const currentStep = currentEntry ? currentEntry.step : null;

  return (
    <section className="rounded-[1.5rem] border border-[var(--line)] bg-[var(--card)] p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            {title}
          </p>
          <p className="mt-1 text-sm leading-7 text-[var(--muted)]">
            {description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {sourceLabel ? (
            <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
              {sourceLabel}
            </span>
          ) : null}
          {onClose ? (
            <button type="button" onClick={onClose} className="button-base button-ghost button-sm button-pill">
              Close Replay
            </button>
          ) : null}
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="mt-4 rounded-[1.25rem] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] px-4 py-6 text-sm leading-7 text-[var(--muted)]">
          {emptyState}
        </div>
      ) : (
        <>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  if (isPlaying) {
                    setIsPlaying(false);
                    return;
                  }

                  if (currentIndex >= entries.length - 1 || currentIndex < 0) {
                    setCurrentIndex(0);
                  }
                  setIsPlaying(entries.length > 1);
                }}
                className="button-base button-primary button-sm button-pill"
              >
                {isPlaying ? "Pause" : replayFinished ? "Replay" : "Play"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentIndex((value) => Math.max(0, value - 1));
                }}
                disabled={currentIndex <= 0}
                className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentIndex((value) => Math.min(entries.length - 1, Math.max(0, value + 1)));
                }}
                disabled={currentIndex >= entries.length - 1}
                className="button-base button-secondary button-sm button-pill disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <label className="surface-pill flex items-center gap-2 rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                Speed
                <select
                  value={speed}
                  onChange={(event) => setSpeed(Number(event.target.value) as (typeof SPEED_OPTIONS)[number])}
                  className="bg-transparent text-[11px] font-semibold text-[var(--foreground)] outline-none"
                >
                  {SPEED_OPTIONS.map((value) => (
                    <option key={value} value={value}>
                      {value}x
                    </option>
                  ))}
                </select>
              </label>
              <span className="surface-pill rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                {Math.max(0, currentIndex + 1)} / {entries.length} events
              </span>
            </div>
          </div>

          <div className="mt-5">
            <div className="relative h-3 rounded-full bg-[var(--surface-soft)]">
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-[var(--accent-solid)] transition-[width] duration-200 ease-out"
                style={{ width: `${progress * 100}%` }}
              />
              {entries.map((entry, index) => {
                const isCurrent = index === currentIndex;
                const isPlayed = index <= currentIndex;

                return (
                  <span
                    key={`${entry.step}-${entry.event}-${index}`}
                    className={joinClasses(
                      "absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 transition-all duration-200 ease-out",
                      isCurrent
                        ? "border-[var(--accent-solid)] bg-[var(--bg)] shadow-[0_0_0_4px_color-mix(in_srgb,var(--accent-solid)_18%,transparent)]"
                        : isPlayed
                          ? "border-[var(--accent-solid)] bg-[var(--accent-solid)]"
                          : "border-[var(--line)] bg-[var(--panel)]",
                    )}
                    style={{ left: `${markerPosition(index, entries.length)}%` }}
                  />
                );
              })}
            </div>
            <div className="mt-2 flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
              <span>{formatReplayTime(entries[0]?.timestamp ?? 0)}</span>
              <span>{formatReplayTime(entries[entries.length - 1]?.timestamp ?? 0)}</span>
            </div>
          </div>

          <div className="mt-5 rounded-[1.25rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                {currentEntry ? formatReplayTime(currentEntry.timestamp) : "+0.00s"}
              </span>
              <span className="rounded-full border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--accent-solid)]">
                {currentEntry ? formatEventLabel(currentEntry.event) : "Ready"}
              </span>
            </div>
            <p className="mt-3 text-base font-semibold text-[var(--foreground)]">
              {currentEntry ? resolvedFormatStepLabel(currentEntry.step) : "Select a replay event"}
            </p>
            <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
              {currentEntry?.data ?? "The replay will surface the current event details here."}
            </p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {stepLabels.map(({ step, label }) => {
              const isActive = currentStep === step;
              const isPlayed = playedEntries.some((entry) => entry.step === step);

              return (
                <span
                  key={step}
                  className={joinClasses(
                    "rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] transition-all duration-200 ease-out",
                    isActive
                      ? "border-[var(--accent-border-soft)] bg-[var(--accent-soft)] text-[var(--accent-solid)]"
                      : isPlayed
                        ? "border-[var(--done-border)] bg-[var(--done-bg)] text-[var(--done-text)]"
                        : "border-[var(--line)] bg-[var(--surface-soft)] text-[var(--muted)]",
                  )}
                >
                  {label}
                </span>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}

export function TimelineReplay(props: TimelineReplayProps) {
  const { autoplayKey, entries } = props;
  const replayKey = [
    String(autoplayKey ?? "default"),
    String(entries.length),
    entries[0]?.timestamp ?? "start",
    entries[0]?.step ?? "start-step",
    entries[entries.length - 1]?.timestamp ?? "end",
    entries[entries.length - 1]?.step ?? "end-step",
  ].join(":");

  return <TimelineReplayInner key={replayKey} {...props} />;
}