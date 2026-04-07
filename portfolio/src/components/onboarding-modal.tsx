"use client";

import { useState } from "react";

const ONBOARDING_KEY = "onboarding-dismissed";

export function OnboardingModal() {
  const [show, setShow] = useState(() => {
    if (typeof window === "undefined") return false;
    return !localStorage.getItem(ONBOARDING_KEY);
  });

  if (!show) return null;

  const dismiss = () => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setShow(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-label="Welcome">
      <div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-[var(--card)] p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-[var(--foreground)]">Welcome to GenAI Systems Lab</h2>
        <ol className="mt-4 space-y-3 text-sm leading-6 text-[var(--muted)]">
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent-solid)]">1</span>
            <span><strong className="text-[var(--foreground)]">Browse 20 AI systems</strong> — each with architecture, features, and live demos.</span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent-solid)]">2</span>
            <span><strong className="text-[var(--foreground)]">Bring your own API key</strong> — keys stay in your browser and are never stored.</span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent-solid)]">3</span>
            <span><strong className="text-[var(--foreground)]">Run any system live</strong> — see real-time output, memory traces, and timeline replays.</span>
          </li>
        </ol>
        <button
          type="button"
          onClick={dismiss}
          className="button-base button-primary button-pill mt-6 w-full"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
