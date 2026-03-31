"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { useTheme } from "next-themes";

const THEME_FADE_DURATION_MS = 240;
const THEME_SWITCH_DELAY_MS = 110;

type ThemeToggleProps = {
  className?: string;
};

function subscribeToMount() {
  return () => {};
}

export function ThemeToggle({ className = "" }: ThemeToggleProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const timeoutIdsRef = useRef<number[]>([]);
  const mounted = useSyncExternalStore(subscribeToMount, () => true, () => false);

  const clearTransitionTimers = () => {
    timeoutIdsRef.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
    timeoutIdsRef.current = [];
  };

  useEffect(() => {
    return () => {
      clearTransitionTimers();
      document.documentElement.classList.remove("theme-fade");
    };
  }, []);

  const isDark = mounted ? resolvedTheme !== "light" : true;
  const nextTheme = isDark ? "light" : "dark";
  const tooltip = mounted
    ? nextTheme === "light"
      ? "Light"
      : "Dark"
    : "Theme";
  const label = mounted
    ? isTransitioning
      ? `Switching to ${nextTheme} theme`
      : `Switch to ${nextTheme} theme`
    : "Toggle theme";

  const handleThemeToggle = () => {
    if (!mounted || isTransitioning) {
      return;
    }

    const root = document.documentElement;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setTheme(nextTheme);
      return;
    }

    clearTransitionTimers();
    setIsTransitioning(true);
    root.classList.add("theme-fade");

    timeoutIdsRef.current = [
      window.setTimeout(() => {
        setTheme(nextTheme);
      }, THEME_SWITCH_DELAY_MS),
      window.setTimeout(() => {
        root.classList.remove("theme-fade");
        setIsTransitioning(false);
        timeoutIdsRef.current = [];
      }, THEME_FADE_DURATION_MS),
    ];
  };

  return (
    <div className="group relative inline-flex">
      <button
        type="button"
        aria-label={label}
        aria-busy={isTransitioning}
        title={label}
        onClick={handleThemeToggle}
        disabled={isTransitioning}
        className={[
          "button-base button-secondary button-icon h-10 w-10",
          "text-base leading-none shadow-[var(--chart-tooltip-shadow)]",
          className,
        ].join(" ")}
      >
        <span className="relative h-5 w-5" aria-hidden="true">
          <span
            className={`absolute inset-0 flex items-center justify-center transition-all duration-250 ${
              isDark
                ? "rotate-0 scale-100 opacity-100"
                : "-rotate-90 scale-75 opacity-0"
            }`}
          >
            🌙
          </span>
          <span
            className={`absolute inset-0 flex items-center justify-center transition-all duration-250 ${
              isDark
                ? "rotate-90 scale-75 opacity-0"
                : "rotate-0 scale-100 opacity-100"
            }`}
          >
            ☀️
          </span>
        </span>
      </button>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2 rounded-full border border-[var(--line)] bg-[var(--card-strong)] px-2.5 py-1 text-[11px] font-medium text-[var(--foreground)] opacity-0 shadow-[var(--chart-tooltip-shadow)] transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:translate-y-0 group-focus-within:opacity-100"
      >
        {tooltip}
      </span>
    </div>
  );
}