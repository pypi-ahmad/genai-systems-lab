"use client";

import { useState } from "react";
import { ONBOARDING_KEY } from "@/components/onboarding-modal";

const GUIDE_KEY = "playground-guide-dismissed";
const SUPPRESS_KEYS = [
  "suppress-clear-session-confirm",
  "suppress-rerun-confirm",
];

export function HelpReset() {
  const [showPanel, setShowPanel] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  function resetAll() {
    localStorage.removeItem(ONBOARDING_KEY);
    localStorage.removeItem(GUIDE_KEY);
    for (const key of SUPPRESS_KEYS) localStorage.removeItem(key);
    setConfirmed(true);
    setTimeout(() => {
      setConfirmed(false);
      setShowPanel(false);
    }, 1800);
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setShowPanel((v) => !v)}
        className="text-xs text-[var(--muted)] underline decoration-[var(--line)] underline-offset-2 transition-colors hover:text-[var(--foreground)]"
      >
        Help &amp; tips
      </button>

      {showPanel && (
        <div className="absolute bottom-full right-0 mb-2 w-64 rounded-[1.25rem] border border-[var(--line)] bg-[var(--card-strong)] p-4 shadow-[var(--chart-tooltip-shadow)]">
          <p className="text-xs font-semibold text-[var(--foreground)]">Reset guides &amp; tips</p>
          <p className="mt-1.5 text-[11px] leading-5 text-[var(--muted)]">
            Re-show the welcome walkthrough, quick-start guide, and all dismissed confirmation dialogs.
          </p>
          <button
            type="button"
            onClick={resetAll}
            disabled={confirmed}
            className="button-base button-secondary button-sm button-pill mt-3 w-full disabled:opacity-60"
          >
            {confirmed ? "Done — reload to see guides" : "Reset all guides"}
          </button>
        </div>
      )}
    </div>
  );
}
