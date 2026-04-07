"use client";

import { useCallback, useEffect, useState } from "react";

type CopyCodeBlockProps = {
  code: string;
  className?: string;
};

export function CopyCodeBlock({ code, className = "" }: CopyCodeBlockProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(false), 1600);
    return () => clearTimeout(id);
  }, [copied]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
    } catch {
      // clipboard unavailable
    }
  }, [code]);

  return (
    <div className="relative">
      <pre className={className}>
        {code}
      </pre>
      <button
        type="button"
        onClick={handleCopy}
        className="absolute right-3 top-3 rounded-lg border border-[var(--line)] bg-[var(--panel)] px-2 py-1 text-[11px] font-medium text-[var(--muted)] opacity-0 transition-opacity hover:text-[var(--foreground)] [div:hover>&]:opacity-100"
      >
        {copied ? "Copied ✓" : "Copy"}
      </button>
    </div>
  );
}
