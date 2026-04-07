"use client";

import { useEffect, useState } from "react";

type FeatureTooltipProps = {
  storageKey: string;
  message: string;
};

export function FeatureTooltip({ storageKey, message }: FeatureTooltipProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (localStorage.getItem(storageKey) !== "1") {
        setVisible(true);
      }
    } catch {
      // localStorage unavailable
    }
  }, [storageKey]);

  if (!visible) return null;

  return (
    <div className="mt-3 flex items-start gap-2 rounded-[1rem] border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-3 py-2">
      <p className="flex-1 text-[11px] leading-5 text-[var(--foreground)]">{message}</p>
      <button
        type="button"
        onClick={() => {
          setVisible(false);
          try { localStorage.setItem(storageKey, "1"); } catch {}
        }}
        className="shrink-0 text-[11px] font-medium text-[var(--muted)] hover:text-[var(--foreground)]"
        aria-label="Dismiss tip"
      >
        ✕
      </button>
    </div>
  );
}
