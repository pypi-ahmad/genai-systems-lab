"use client";

import { useState } from "react";
import { runProject } from "@/lib/api";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { getStoredAuthToken } from "@/lib/auth";

export default function DemoButton({
  projectName,
  defaultInput,
}: {
  projectName: string;
  defaultInput: string;
}) {
  const [input, setInput] = useState(defaultInput);
  const [output, setOutput] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authToken] = useState<string | null>(() => getStoredAuthToken());
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());

  async function handleRun() {
    setLoading(true);
    setError(null);
    setOutput(null);

    const normalizedApiKey = apiKey.trim();
    if (!normalizedApiKey) {
      setError("Enter a Google API key before running this demo.");
      setLoading(false);
      return;
    }

    let body: Record<string, unknown>;
    try {
      body = JSON.parse(input);
    } catch {
      setError("Invalid JSON input");
      setLoading(false);
      return;
    }

    try {
      const result = await runProject(projectName, body, authToken ?? undefined, normalizedApiKey);
      if (result.ok) {
        setOutput(JSON.stringify(result.data, null, 2));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <label
          htmlFor="demo-input"
          className="block text-sm font-medium text-[var(--muted)]"
        >
          Request body
        </label>
        <textarea
          id="demo-input"
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          spellCheck={false}
          className="input-shell w-full rounded-lg p-3 font-mono text-sm leading-relaxed"
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="demo-api-key"
          className="block text-sm font-medium text-[var(--muted)]"
        >
          Google API key
        </label>
        <input
          id="demo-api-key"
          type="password"
          value={apiKey}
          onChange={(event) => {
            const nextApiKey = event.target.value;
            setApiKey(nextApiKey);
            setStoredApiKey(nextApiKey.trim());
          }}
          autoComplete="off"
          spellCheck={false}
          placeholder="AIza..."
          className="input-shell w-full rounded-lg p-3 font-mono text-sm leading-relaxed"
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleRun}
          disabled={loading}
          className="button-base button-primary disabled:opacity-50"
        >
          {loading && (
            <svg
              className="h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          )}
          {loading ? "Running…" : "Run Demo"}
        </button>
        <span className="text-xs text-[var(--muted)]">
          POST /{projectName}/run
        </span>
      </div>

      <p className="text-xs leading-6 text-[var(--muted)]">
        {authToken ? "Signed in: successful runs are saved to your history." : "Guest mode: you can run demos without signing in, but history and replay stay unavailable."}
      </p>

      {error && (
        <div className="error-panel rounded-lg p-3">
          <p className="text-sm font-medium text-[var(--danger-text)]">
            Error
          </p>
          <p className="mt-1 text-sm text-[var(--danger-text-soft)]">
            {error}
          </p>
        </div>
      )}

      {output && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-[var(--muted)]">Response</p>
          <pre className="input-shell max-h-96 overflow-auto rounded-lg p-4 text-sm leading-relaxed">
            {output}
          </pre>
        </div>
      )}
    </div>
  );
}
