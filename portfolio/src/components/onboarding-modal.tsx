"use client";

import { useState } from "react";
import Link from "next/link";

const STORAGE_KEY = "onboarding-modal-seen";

export function OnboardingModal() {
  const [open, setOpen] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem(STORAGE_KEY) !== "1";
    } catch {
      return false;
    }
  });

  function dismiss() {
    setOpen(false);
    try { localStorage.setItem(STORAGE_KEY, "1"); } catch {}
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4" onClick={dismiss}>
      <div
        className="relative w-full max-w-md space-y-6 rounded-2xl border border-[var(--line)] bg-[var(--card)] p-6 shadow-xl sm:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={dismiss}
          className="absolute right-4 top-4 text-[var(--muted)] hover:text-[var(--foreground)]"
          aria-label="Close"
        >
          ✕
        </button>

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--accent-solid)]">Welcome</p>
          <h2 className="mt-2 text-2xl font-semibold text-[var(--foreground)]">GenAI Systems Lab</h2>
          <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
            Explore 20 production-grade AI systems spanning retrieval, orchestration, and multi-agent workflows.
          </p>
        </div>

        <div className="space-y-3">
          <div className="surface-panel rounded-xl px-4 py-3">
            <p className="text-sm font-semibold text-[var(--foreground)]">① Browse projects</p>
            <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">See what each system does and how it works.</p>
          </div>
          <div className="surface-panel rounded-xl px-4 py-3">
            <p className="text-sm font-semibold text-[var(--foreground)]">② Try the playground</p>
            <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">Run any system live with your own API key (BYOK).</p>
          </div>
          <div className="surface-panel rounded-xl px-4 py-3">
            <p className="text-sm font-semibold text-[var(--foreground)]">③ Get your API key</p>
            <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">You&apos;ll need an OpenAI or provider key. Your key stays in your browser only.</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/playground"
            onClick={dismiss}
            className="button-base button-primary button-sm button-pill"
          >
            Open Playground
          </Link>
          <button
            type="button"
            onClick={dismiss}
            className="button-base button-secondary button-sm button-pill"
          >
            Explore on my own
          </button>
        </div>
      </div>
    </div>
  );
}
