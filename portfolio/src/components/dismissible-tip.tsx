"use client";

import { useState } from "react";

/**
 * A one-line dismissible tooltip that shows once per `storageKey`.
 * After dismissal, it never renders again for this browser.
 */
export function DismissibleTip({
  storageKey,
  text,
  className = "",
}: {
  storageKey: string;
  text: string;
  className?: string;
}) {
  const [visible, setVisible] = useState(() => {
    if (typeof window === "undefined") return false;
    return !localStorage.getItem(storageKey);
  });

  if (!visible) return null;

  return (
    <div className={`flex items-start justify-between gap-2 rounded-xl border border-[var(--accent-border-soft)] bg-[var(--accent-soft)] px-3 py-2 text-xs leading-5 text-[var(--muted)] ${className}`}>
      <span>{text}</span>
      <button
        type="button"
        onClick={() => {
          localStorage.setItem(storageKey, "true");
          setVisible(false);
        }}
        className="shrink-0 text-[var(--muted)] hover:text-[var(--foreground)]"
        aria-label="Dismiss tip"
      >
        ✕
      </button>
    </div>
  );
}
