"use client";

import { useCallback, useEffect, useState } from "react";

export function CopyButton({ text, className = "" }: { text: string; className?: string }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(id);
  }, [copied]);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      // Silently fail if clipboard is unavailable
    }
  }, [text]);

  return (
    <button
      type="button"
      onClick={() => void copy()}
      className={`button-base button-ghost button-sm button-pill ${className}`}
      aria-label={copied ? "Copied" : "Copy to clipboard"}
    >
      {copied ? "Copied ✓" : "Copy"}
    </button>
  );
}
