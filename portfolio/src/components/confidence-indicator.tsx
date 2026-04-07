"use client";

import { useState } from "react";

type ConfidenceIndicatorProps = {
  confidence: number | null | undefined;
  compact?: boolean;
  className?: string;
};

function clampConfidence(value: number) {
  return Math.max(0, Math.min(1, value));
}

function confidenceTone(confidence: number) {
  if (confidence > 0.75) {
    return {
      dot: "bg-[var(--success-dot)]",
      text: "text-[var(--success-text)]",
      border: "border-[color-mix(in_srgb,var(--success-dot)_26%,var(--line))]",
      fill: "var(--success-dot)",
    };
  }

  if (confidence >= 0.5) {
    return {
      dot: "bg-[var(--warning-text)]",
      text: "text-[var(--warning-text)]",
      border: "border-[color-mix(in_srgb,var(--warning-text)_26%,var(--line))]",
      fill: "var(--warning-text)",
    };
  }

  return {
    dot: "bg-[var(--danger-text)]",
    text: "text-[var(--danger-text)]",
    border: "border-[color-mix(in_srgb,var(--danger-text)_26%,var(--line))]",
    fill: "var(--danger-text)",
  };
}

function InfoTooltip() {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="inline-flex items-center justify-center rounded-full text-[var(--muted)] transition-colors hover:text-[var(--foreground)]"
        aria-label="What is confidence?"
      >
        <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5" aria-hidden="true">
          <path fillRule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm.75-10.25a.75.75 0 0 0-1.5 0v.01a.75.75 0 0 0 1.5 0v-.01ZM8 7a.75.75 0 0 0-.75.75v3.5a.75.75 0 0 0 1.5 0v-3.5A.75.75 0 0 0 8 7Z" clipRule="evenodd" />
        </svg>
      </button>
      {open && (
        <span className="absolute bottom-full left-1/2 z-50 mb-2 w-56 -translate-x-1/2 rounded-xl border border-[var(--line)] bg-[var(--panel)] px-3 py-2 text-[11px] leading-5 text-[var(--foreground)] shadow-lg">
          Confidence reflects the system&apos;s self-assessed certainty in its output. Higher is better.
        </span>
      )}
    </span>
  );
}

export function ConfidenceIndicator({ confidence, compact = false, className = "" }: ConfidenceIndicatorProps) {
  if (typeof confidence !== "number" || Number.isNaN(confidence)) {
    return null;
  }

  const normalized = clampConfidence(confidence);
  const percent = Math.round(normalized * 100);
  const tone = confidenceTone(normalized);
  const tooltip = "Confidence based on execution success, evaluation, and consistency";

  if (compact) {
    return (
      <span
        title={tooltip}
        className={`surface-pill inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${tone.border} ${tone.text} ${className}`.trim()}
      >
        <span className={`h-2 w-2 rounded-full ${tone.dot}`} />
        {percent}% confidence
        <InfoTooltip />
      </span>
    );
  }

  return (
    <div
      title={tooltip}
      className={`surface-panel rounded-[1rem] border px-4 py-3 ${tone.border} ${className}`.trim()}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${tone.dot}`} />
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Confidence</p>
          <InfoTooltip />
        </div>
        <p className={`text-sm font-semibold ${tone.text}`}>{percent}%</p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--surface-soft)]">
        <div
          className="h-full rounded-full transition-[width] duration-300 ease-out"
          style={{ width: `${percent}%`, backgroundColor: tone.fill }}
        />
      </div>
    </div>
  );
}