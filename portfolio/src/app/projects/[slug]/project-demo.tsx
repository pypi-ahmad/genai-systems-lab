"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchCurrentUser, getApiUrl, runProject } from "@/lib/api";
import { getStoredApiKey, setStoredApiKey } from "@/lib/apikey";
import { getStoredAuthSession, storeAuthSession } from "@/lib/auth";

interface ProjectDemoProps {
  apiEndpoint: string;
  exampleInput: string;
  title?: string;
  description?: string;
  ctaLabel?: string;
}

function projectApiName(apiEndpoint: string) {
  return apiEndpoint.replace(/^\//, "").replace(/\/run$/, "");
}

function formatResult(value: unknown) {
  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export default function ProjectDemo({
  apiEndpoint,
  exampleInput,
  title,
  description,
  ctaLabel,
}: ProjectDemoProps) {
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [result, setResult] = useState<string>("");
  const [input, setInput] = useState(exampleInput);
  const [authToken, setAuthToken] = useState<string | null>(() => getStoredAuthSession());
  const [apiKey, setApiKey] = useState(() => getStoredApiKey());
  const projectName = projectApiName(apiEndpoint);

  useEffect(() => {
    if (authToken) {
      return;
    }

    let cancelled = false;
    void fetchCurrentUser()
      .then((user) => {
        if (cancelled || !user) {
          return;
        }
        storeAuthSession();
        setAuthToken(getStoredAuthSession());
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, [authToken]);

  async function handleRun() {
    setStatus("running");
    setResult("");

    const normalizedApiKey = apiKey.trim();
    if (!normalizedApiKey) {
      setStatus("error");
      setResult("Enter a Google API key before running this demo.");
      return;
    }

    let body: Record<string, unknown>;
    try {
      body = JSON.parse(input);
    } catch {
      setStatus("error");
      setResult("Input is not valid JSON.");
      return;
    }

    try {
      const response = await runProject(projectName, body, authToken ?? undefined, normalizedApiKey);

      if (!response.ok) {
        setStatus("error");
        setResult(response.error);
        return;
      }

      setStatus("success");
      setResult(formatResult(response.data));
    } catch (error) {
      setStatus("error");
      setResult(error instanceof Error ? error.message : "Unable to run demo.");
    }
  }

  return (
    <section className="surface-card rounded-xl p-6 sm:p-8">
      <p className="eyebrow">Run Demo</p>
      <h3 className="mt-3 text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">
        {title ?? "Test the live endpoint"}
      </h3>
      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
        {description ?? "Edit the JSON body and send it to the FastAPI backend for this project."}
      </p>

      <div className="surface-panel mt-4 rounded-[1.25rem] px-4 py-3 font-mono text-xs leading-6 text-[var(--muted)]">
        POST {getApiUrl(`/${projectName}/run`)}
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Google API Key
          </span>
          <input
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
            className="input-shell mt-3 w-full rounded-[1rem] px-4 py-3 font-mono text-xs leading-6"
          />
        </label>
        <div className="surface-panel rounded-[1rem] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
          {authToken ? (
            <span>Signed in. This run can be saved to your history.</span>
          ) : (
            <span>
              Guest mode is available. <Link href="/auth" className="font-semibold text-[var(--foreground)] underline decoration-[var(--accent-border-soft)] underline-offset-2 hover:text-[var(--accent-solid)] hover:decoration-[var(--accent-solid)]">
                Sign in
              </Link>{" "}
              to save history and replay runs.
            </span>
          )}
        </div>
      </div>

      <div className="mt-5">
        <label
          htmlFor={`demo-input-${projectName}`}
          className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]"
        >
          Request Body
        </label>
        <textarea
          id={`demo-input-${projectName}`}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          spellCheck={false}
          rows={10}
          className="input-shell mt-3 w-full rounded-[1.25rem] px-4 py-4 font-mono text-[13px] leading-7"
        />
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={status === "running"}
        className="button-base button-primary button-pill mt-5 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {status === "running" ? "Running..." : (ctaLabel ?? "Run Demo")}
      </button>

      {status === "running" ? (
        <div className="surface-panel mt-5 rounded-[1.25rem] p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Loading
          </p>
          <div className="mt-3 flex items-center gap-3 text-sm leading-7 text-[var(--muted)]">
            <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
            <span>Waiting for the FastAPI response.</span>
          </div>
        </div>
      ) : null}

      {result && status !== "running" ? (
        <div
          className={`mt-5 rounded-[1.25rem] border p-4 ${
            status === "error"
              ? "error-panel"
              : "surface-panel"
          }`}
        >
          <p
            className={`mb-3 text-xs font-semibold uppercase tracking-[0.18em] ${
              status === "error"
                ? "text-[var(--danger-text)]"
                : "text-[var(--muted)]"
            }`}
          >
            {status === "error" ? "Demo Error" : "Demo Output"}
          </p>
          <pre
            className={`overflow-x-auto rounded-[1rem] p-4 font-mono text-[13px] leading-7 ${
              status === "error"
                ? "bg-[var(--danger-surface)] text-[var(--danger-text-soft)]"
                : "input-shell"
            }`}
          >
            {result}
          </pre>
        </div>
      ) : null}
    </section>
  );
}