"use client";

import { useCallback, useState, type Dispatch, type SetStateAction } from "react";
import type { HistoryRun, RunExplanation } from "@/lib/api";
import { explainRun, shareRun, unshareRun } from "@/lib/api";
import type { TimelineReplayFrame } from "@/components/TimelineReplay";
import type { ExecuteRunOverrides } from "./use-playground-run";

export interface PlaygroundHistoryDeps {
  authToken: string | null;
  apiKey: string;
  appendLog: (message: string) => void;
  disconnect: () => void;
  executeRun: (streamMode: boolean, apiKey: string, overrides?: ExecuteRunOverrides) => void;
  hydrateSavedRun: (historyRun: HistoryRun) => void;
  scrollOutputIntoView: () => void;
  setHistoryRuns: Dispatch<SetStateAction<HistoryRun[]>>;
  streamMode: boolean;
}

export function usePlaygroundHistory({
  authToken,
  apiKey,
  appendLog,
  disconnect,
  executeRun,
  hydrateSavedRun,
  scrollOutputIntoView,
  setHistoryRuns,
  streamMode,
}: PlaygroundHistoryDeps) {
  const [activeReplayRun, setActiveReplayRun] = useState<HistoryRun | null>(null);
  const [replayFrame, setReplayFrame] = useState<TimelineReplayFrame | null>(null);
  const [replayAutoplayKey, setReplayAutoplayKey] = useState(0);
  const [runExplanations, setRunExplanations] = useState<Record<number, RunExplanation>>({});
  const [activeExplanationRun, setActiveExplanationRun] = useState<HistoryRun | null>(null);
  const [explainingRunId, setExplainingRunId] = useState<number | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [sharingRunId, setSharingRunId] = useState<number | null>(null);

  const clearReplay = useCallback(() => {
    setActiveReplayRun(null);
    setReplayFrame(null);
  }, []);

  const clearExplanation = useCallback(() => {
    setActiveExplanationRun(null);
    setExplainingRunId(null);
    setExplanationError(null);
  }, []);

  const handleHistoryReplay = useCallback((historyRun: HistoryRun) => {
    disconnect();
    clearReplay();
    hydrateSavedRun(historyRun);
    setActiveReplayRun(historyRun);
    setReplayFrame(null);
    setReplayAutoplayKey((value) => value + 1);
    scrollOutputIntoView();
  }, [clearReplay, disconnect, hydrateSavedRun, scrollOutputIntoView]);

  const handleHistoryExplain = useCallback(async (historyRun: HistoryRun) => {
    if (!authToken) {
      setExplanationError("Sign in is required to generate saved-run explanations.");
      return;
    }

    if (activeExplanationRun?.id === historyRun.id && Boolean(runExplanations[historyRun.id])) {
      clearExplanation();
      return;
    }

    setActiveExplanationRun(historyRun);
    setExplanationError(null);

    if (runExplanations[historyRun.id]) {
      return;
    }

    setExplainingRunId(historyRun.id);

    try {
      const explanation = await explainRun(historyRun.id, authToken, apiKey || undefined);
      setRunExplanations((previous) => ({
        ...previous,
        [historyRun.id]: explanation,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to explain this saved run.";
      setExplanationError(message);
    } finally {
      setExplainingRunId((value) => (value === historyRun.id ? null : value));
    }
  }, [activeExplanationRun?.id, apiKey, authToken, clearExplanation, runExplanations]);

  const handleHistoryRerun = useCallback((historyRun: HistoryRun) => {
    clearReplay();
    clearExplanation();
    void executeRun(streamMode, apiKey, { slug: historyRun.project, inputText: historyRun.input });
  }, [apiKey, clearExplanation, clearReplay, executeRun, streamMode]);

  const handleShare = useCallback(async (historyRun: HistoryRun) => {
    if (!authToken) {
      return;
    }

    setSharingRunId(historyRun.id);

    try {
      const response = await shareRun(historyRun.id, authToken);
      setHistoryRuns((previous) => previous.map((run) => (
        run.id === historyRun.id
          ? { ...run, share_token: response.share_token, is_public: true, expires_at: response.expires_at }
          : run
      )));
      const shareUrl = `${window.location.origin}/run/${response.share_token}`;
      await navigator.clipboard.writeText(shareUrl);
      appendLog(`Shared run #${historyRun.id} - link copied to clipboard`);
    } catch {
      appendLog(`Failed to share run #${historyRun.id}`);
    } finally {
      setSharingRunId(null);
    }
  }, [appendLog, authToken, setHistoryRuns]);

  const handleUnshare = useCallback(async (historyRun: HistoryRun) => {
    if (!authToken) {
      return;
    }

    setSharingRunId(historyRun.id);

    try {
      await unshareRun(historyRun.id, authToken);
      setHistoryRuns((previous) => previous.map((run) => (
        run.id === historyRun.id
          ? { ...run, share_token: null, is_public: false, expires_at: null }
          : run
      )));
      appendLog(`Unshared run #${historyRun.id}`);
    } catch {
      appendLog(`Failed to unshare run #${historyRun.id}`);
    } finally {
      setSharingRunId(null);
    }
  }, [appendLog, authToken, setHistoryRuns]);

  return {
    activeExplanationRun,
    activeReplayRun,
    clearExplanation,
    clearReplay,
    explanationError,
    explainingRunId,
    handleHistoryExplain,
    handleHistoryReplay,
    handleHistoryRerun,
    handleShare,
    handleUnshare,
    replayAutoplayKey,
    replayFrame,
    runExplanations,
    setReplayFrame,
    setRunExplanations,
    sharingRunId,
  };
}