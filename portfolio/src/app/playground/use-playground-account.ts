"use client";

import { useCallback, useEffect, useState } from "react";
import { clearRunSession, fetchCurrentUser, fetchHistory, fetchRunSession } from "@/lib/api";
import type { HistoryRun } from "@/lib/api";
import { clearAuthToken, getStoredAuthToken, storeAuthToken } from "@/lib/auth";
import { clearStoredSessionId, getStoredSessionId, storeSessionId } from "@/lib/session";
import { isRunMemoryEntry, isRunTimelineEntry } from "./playground-utils";

export function usePlaygroundAccount() {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [sessionMemoryPreview, setSessionMemoryPreview] = useState<string[]>([]);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [clearingSession, setClearingSession] = useState(false);
  const [historyRuns, setHistoryRuns] = useState<HistoryRun[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const clearLocalSession = useCallback(() => {
    setActiveSessionId(null);
    setSessionMemoryPreview([]);
    clearStoredSessionId();
  }, []);

  const applySessionState = useCallback((sessionId: number | null, memory: string[]) => {
    if (sessionId === null) {
      clearLocalSession();
      return;
    }

    setActiveSessionId(sessionId);
    setSessionMemoryPreview(memory.slice(-5));
    storeSessionId(sessionId);
  }, [clearLocalSession]);

  const loadSession = useCallback(async (sessionId: number, token: string) => {
    setSessionLoading(true);
    try {
      const response = await fetchRunSession(sessionId, token);
      applySessionState(response.id, response.memory);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load session.";
      if (message.startsWith("401") || message.startsWith("404")) {
        clearLocalSession();
      }
    } finally {
      setSessionLoading(false);
    }
  }, [applySessionState, clearLocalSession]);

  const refreshHistory = useCallback(async (token: string) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await fetchHistory(token);
      setHistoryRuns(
        response.runs.map((run) => ({
          ...run,
          memory: Array.isArray(run.memory) ? run.memory.filter(isRunMemoryEntry) : [],
          timeline: Array.isArray(run.timeline) ? run.timeline.filter(isRunTimelineEntry) : [],
        })),
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load history.";
      setHistoryError(message);
      if (message.startsWith("401")) {
        clearAuthToken();
        setAuthToken(null);
        setHistoryRuns([]);
        clearLocalSession();
      }
    } finally {
      setHistoryLoading(false);
    }
  }, [clearLocalSession]);

  const clearSession = useCallback(async () => {
    if (!authToken || activeSessionId === null) {
      return false;
    }

    setClearingSession(true);
    try {
      const response = await clearRunSession(activeSessionId, authToken);
      applySessionState(response.id, response.memory);
      return true;
    } catch {
      return false;
    } finally {
      setClearingSession(false);
    }
  }, [activeSessionId, applySessionState, authToken]);

  useEffect(() => {
    let cancelled = false;

    async function hydrateAuthState() {
      let token = getStoredAuthToken();

      if (!token) {
        const currentUser = await fetchCurrentUser().catch(() => null);
        if (currentUser) {
          storeAuthToken("");
          token = getStoredAuthToken();
        } else {
          clearAuthToken();
        }
      }

      if (cancelled) {
        return;
      }

      setAuthToken(token);
      if (!token) {
        clearLocalSession();
        return;
      }

      void refreshHistory(token);
      const storedSessionId = getStoredSessionId();
      if (storedSessionId !== null) {
        void loadSession(storedSessionId, token);
      }
    }

    void hydrateAuthState();

    return () => {
      cancelled = true;
    };
  }, [clearLocalSession, loadSession, refreshHistory]);

  return {
    activeSessionId,
    applySessionState,
    authToken,
    clearLocalSession,
    clearSession,
    clearingSession,
    historyError,
    historyLoading,
    historyRuns,
    refreshHistory,
    sessionLoading,
    sessionMemoryPreview,
    setAuthToken,
    setHistoryError,
    setHistoryRuns,
  };
}