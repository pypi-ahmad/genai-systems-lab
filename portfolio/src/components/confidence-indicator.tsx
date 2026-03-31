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