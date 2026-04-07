"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchAuthConfig, fetchCurrentUser, login, logout, signup } from "@/lib/api";
import { clearAuthSession, getStoredAuthSession, storeAuthSession } from "@/lib/auth";

type Mode = "login" | "signup";

function ModeButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`button-base button-sm button-pill ${
        active
          ? "button-primary"
          : "button-ghost"
      }`}
    >
      {label}
    </button>
  );
}

export default function AuthClient() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionExists, setSessionExists] = useState(() => Boolean(getStoredAuthSession()));
  const [publicSignupEnabled, setPublicSignupEnabled] = useState(true);

  useEffect(() => {
    let cancelled = false;

    void fetchAuthConfig()
      .then((config) => {
        if (cancelled) {
          return;
        }
        setPublicSignupEnabled(config.public_signup);
        if (!config.public_signup) {
          setMode((previous) => (previous === "signup" ? "login" : previous));
        }
      })
      .catch(() => undefined);

    void fetchCurrentUser()
      .then((user) => {
        if (cancelled) {
          return;
        }

        if (user) {
          storeAuthSession();
          setSessionExists(true);
          return;
        }

        clearAuthSession();
        setSessionExists(false);
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const action = mode === "signup" ? signup : login;
      await action(email.trim(), password);
      storeAuthSession();
      setSessionExists(true);
      router.push("/playground");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Clear the local auth marker even if the backend session is already gone.
    }
    clearAuthSession();
    setSessionExists(false);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
      <section className="space-y-6">
        <p className="eyebrow">User Auth</p>
        <h1 className="heading-display text-4xl sm:text-5xl">
          Save runs, keep history, and replay prior prompts.
        </h1>
        <p className="copy-lead max-w-2xl text-base sm:text-lg">
          Sign in with your email and password to save runs, track history, and replay past prompts.
        </p>

        <div className="surface-card rounded-xl p-6 sm:p-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            What this unlocks
          </p>
          <div className="mt-5 grid gap-6 text-sm leading-7 text-[var(--foreground)]">
            <div className="surface-panel rounded-[1.25rem] px-4 py-4">
              Run any project through the protected API.
            </div>
            <div className="surface-panel rounded-[1.25rem] px-4 py-4">
              Persist input, output, project, latency, and timestamp automatically.
            </div>
            <div className="surface-panel rounded-[1.25rem] px-4 py-4">
              Re-run saved executions from the playground with one click.
            </div>
          </div>
        </div>
      </section>

      <section className="surface-card rounded-xl p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
              Account Access
            </p>
            <h2 className="heading-section mt-2 text-3xl">
              {mode === "login" ? "Log in" : "Create account"}
            </h2>
          </div>
          <div className="surface-pill flex items-center gap-2 rounded-full p-1">
            <ModeButton active={mode === "login"} label="Log in" onClick={() => setMode("login")} />
            {publicSignupEnabled ? (
              <ModeButton active={mode === "signup"} label="Sign up" onClick={() => setMode("signup")} />
            ) : null}
          </div>
        </div>

        {!publicSignupEnabled ? (
          <div className="surface-panel mt-6 rounded-[1.25rem] p-4 text-sm leading-7 text-[var(--muted)]">
            Public sign-up is currently disabled. Access is reserved for the portfolio owner.
          </div>
        ) : null}

        <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
          <label className="block space-y-2 text-sm font-medium text-[var(--foreground)]">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              className="input-shell w-full rounded-2xl px-4 py-3 text-sm"
            />
          </label>

          <label className="block space-y-2 text-sm font-medium text-[var(--foreground)]">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={8}
              required
              className="input-shell w-full rounded-2xl px-4 py-3 text-sm"
            />
            <span className="flex items-center gap-1.5 text-[11px] text-[var(--muted)]">
              {password.length >= 8 ? (
                <span className="text-[var(--success-dot)]">✓</span>
              ) : (
                <span className="opacity-60">○</span>
              )}
              At least 8 characters
            </span>
          </label>

          {error && (
            <div className="error-panel rounded-[1.25rem] px-4 py-3 text-sm text-[var(--danger-text-soft)]">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="button-base button-primary button-lg button-pill disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Submitting…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>

        <div className="surface-panel mt-6 rounded-[1.25rem] p-4 text-sm leading-7 text-[var(--muted)]">
          {sessionExists ? (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>An authenticated session is already active in this browser.</span>
              <button
                type="button"
                onClick={handleLogout}
                className="button-base button-secondary button-pill"
              >
                Log out
              </button>
            </div>
          ) : (
            <span>
              After authentication, head to <Link href="/playground" className="font-semibold text-[var(--foreground)] underline decoration-[var(--accent-border-soft)] underline-offset-2 transition-colors duration-200 ease-in-out hover:text-[var(--accent-solid)] hover:decoration-[var(--accent-solid)]">the playground</Link> to run projects and review history.
            </span>
          )}
        </div>
      </section>
    </div>
  );
}