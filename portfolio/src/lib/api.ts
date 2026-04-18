import { AUTH_SESSION_MARKER } from "@/lib/auth";
import type { LLMProviderId } from "@/lib/apikey";

const DEFAULT_API_BASE = "http://localhost:8000";
const LOCAL_FALLBACK_API_BASE = "http://127.0.0.1:8001";
const IS_PROD = process.env.NODE_ENV === "production";

function normalizeApiBase(rawValue?: string): string {
  const value = rawValue?.trim();
  if (!value) {
    return DEFAULT_API_BASE;
  }
  return value.replace(/\/+$/, "");
}

const CONFIGURED_API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_BASE_URL);
// In production, never fall back to loopback origins — if the configured
// base fails, surface a real error instead of silently trying to hit the
// end-user's own machine.
const API_BASES = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  ? [CONFIGURED_API_BASE]
  : IS_PROD
    ? [CONFIGURED_API_BASE]
    : [DEFAULT_API_BASE, LOCAL_FALLBACK_API_BASE];
let activeApiBase = API_BASES[0];

function isLocalHostname(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function formatApiReachabilityError(candidates: string[], lastError: unknown): Error {
  const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const browserHostname = typeof window !== "undefined" ? window.location.hostname : null;
  const lastMessage = lastError instanceof Error && lastError.message
    ? ` (${lastError.message})`
    : "";

  if (!configuredBase && browserHostname && !isLocalHostname(browserHostname)) {
    return new Error(
      `Unable to reach the backend server. The API is not configured for this deployment.${lastMessage}`,
    );
  }

  return new Error(
    `Unable to reach the backend server. Make sure it is running and try again.${lastMessage}`,
  );
}

function buildApiUrl(base: string, path: string): string {
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function apiBaseCandidates(): string[] {
  return [activeApiBase, ...API_BASES.filter((base) => base !== activeApiBase)];
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  let lastError: unknown;
  const candidates = apiBaseCandidates();

  for (const base of candidates) {
    try {
      const response = await fetch(buildApiUrl(base, path), {
        credentials: "include",
        ...init,
      });
      activeApiBase = base;
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  throw formatApiReachabilityError(candidates, lastError);
}

export interface LLMRequestOptions {
  provider?: LLMProviderId;
  model?: string;
  apiKey?: string;
}

function authHeaders(token?: string, llm?: LLMRequestOptions): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token && token !== AUTH_SESSION_MARKER) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (llm?.apiKey) {
    headers["X-API-Key"] = llm.apiKey;
  }

  if (llm?.provider) {
    headers["X-LLM-Provider"] = llm.provider;
  }

  if (llm?.model) {
    headers["X-LLM-Model"] = llm.model;
  }

  return headers;
}

function parseErrorMessage(raw: string, fallback: string): string {
  if (!raw) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(raw) as { detail?: unknown; error?: unknown };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (typeof parsed.error === "string") {
      return parsed.error;
    }
  } catch {
    // Fall back to the raw response text when it is not JSON.
  }

  return raw;
}

/** Map HTTP status codes and raw server messages to user-friendly text. */
function humanizeError(status: number, rawMessage: string): string {
  const friendly: Record<number, string> = {
    400: "The request was invalid. Check your input and try again.",
    401: "You are not logged in or your session has expired. Please sign in again.",
    403: "You don't have permission to do that.",
    404: "The requested resource was not found.",
    408: "The request timed out. Try again in a moment.",
    422: "Some of the input could not be processed. Review and try again.",
    429: "Too many requests — please wait a moment and retry.",
    500: "Something went wrong on the server. Try again shortly.",
    502: "The server is temporarily unreachable. Try again in a moment.",
    503: "The service is temporarily unavailable. Try again shortly.",
    504: "The server took too long to respond. Try again in a moment.",
  };

  if (/api.key|api key|x-api-key|missing x-api-key/i.test(rawMessage)) {
    return "API key missing or invalid. Double-check your key and try again.";
  }
  if (/rate.limit/i.test(rawMessage)) {
    return "Rate limit reached. Wait a moment and try again.";
  }
  if (/model.*not found|model.*not available/i.test(rawMessage)) {
    return "The selected model is not available. Choose a different model.";
  }

  return friendly[status] ?? rawMessage;
}

/** Error detail separator used to bundle a friendly message with raw details. */
const ERROR_DETAIL_SEP = "\n---DETAIL---\n";

function formatRunError(status: number, statusText: string, raw: string): string {
  const parsed = parseErrorMessage(raw, statusText);
  const friendly = humanizeError(status, parsed);
  // Always include raw detail so the UI can offer a "Show details" toggle.
  const detail = `${status} ${statusText}${parsed ? `: ${parsed}` : ""}`;
  if (detail && detail !== friendly) {
    return `${friendly}${ERROR_DETAIL_SEP}${detail}`;
  }
  return friendly;
}

/**
 * Split a potentially compound error message into the user-friendly part
 * and the optional raw technical detail.
 */
export function splitErrorDetail(msg: string): { friendly: string; detail: string | null } {
  const idx = msg.indexOf(ERROR_DETAIL_SEP);
  if (idx === -1) return { friendly: msg, detail: null };
  return { friendly: msg.slice(0, idx), detail: msg.slice(idx + ERROR_DETAIL_SEP.length) };
}

// ── Types ────────────────────────────────────────────────

export interface RunResult {
  ok: true;
  data: ProjectRunResponse;
}

export interface RunError {
  ok: false;
  error: string;
}

export interface ProjectMetrics {
  name: string;
  latency: number;
  success_rate: number;
}

export type MetricsTimeRange = "hour" | "day" | "week";

export interface TimeSeriesMetricPoint {
  timestamp: string;
  latency: number;
  confidence: number;
  success: boolean;
}

export interface MetricsResponse {
  total_requests: number;
  avg_latency: number;
  success_rate: number;
  projects: ProjectMetrics[];
}

export interface AuthUser {
  id: number;
  email: string;
}

export interface AuthConfigResponse {
  public_signup: boolean;
}

export interface LLMModelOption {
  id: string;
  label: string;
  provider: LLMProviderId;
}

export interface LLMProviderInfo {
  id: LLMProviderId;
  label: string;
  requires_api_key: boolean;
  api_key_label: string;
  api_key_help_url: string | null;
  api_key_placeholder: string;
  available: boolean;
  unavailable_reason: string | null;
  models: LLMModelOption[];
}

export interface LLMCatalogResponse {
  default_model: string;
  providers: LLMProviderInfo[];
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export interface RunMemoryEntry {
  step: string;
  content: string;
  type: "thought" | "action" | "observation";
}

export interface RunTimelineEntry {
  timestamp: number;
  step: string;
  event: string;
  data: string;
}

export interface RunExplanationStep {
  step: string;
  what_happened: string;
  why_it_mattered: string;
}

export interface RunExplanationDecision {
  decision: string;
  reason: string;
}

export interface RunExplanation {
  steps_taken: RunExplanationStep[];
  key_decisions: RunExplanationDecision[];
  final_reasoning: string;
  final_outcome: string;
}

export interface ProjectRunResponse {
  output: string;
  latency: number;
  confidence: number;
  session_id: number | null;
  session_memory: string[];
  used_session_context: boolean;
  success: boolean;
  memory: RunMemoryEntry[];
  timeline: RunTimelineEntry[];
}

export interface HistoryRun {
  id: number;
  user_id: number;
  session_id: number | null;
  project: string;
  input: string;
  output: string;
  memory: RunMemoryEntry[];
  timeline: RunTimelineEntry[];
  latency: number;
  confidence: number;
  success: boolean;
  timestamp: string | null;
  share_token: string | null;
  is_public: boolean;
  expires_at: string | null;
}

export interface HistoryResponse {
  count: number;
  runs: HistoryRun[];
}

export interface RunSessionState {
  id: number;
  user_id: number;
  memory: string[];
  entry_count: number;
  updated_at: string | null;
}


// ── API calls ────────────────────────────────────────────

export async function runProject(
  projectName: string,
  input: Record<string, unknown>,
  token?: string,
  llm?: LLMRequestOptions,
): Promise<RunResult | RunError> {
  const res = await apiFetch(`/${projectName}/run`, {
    method: "POST",
    headers: authHeaders(token, llm),
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return {
      ok: false,
      error: formatRunError(res.status, res.statusText, text),
    };
  }

  const data = await res.json();
  return { ok: true, data };
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await apiFetch("/metrics", { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMetricsTime(options: {
  project?: string;
  range?: MetricsTimeRange;
} = {}): Promise<TimeSeriesMetricPoint[]> {
  const params = new URLSearchParams();

  if (options.project) {
    params.set("project", options.project);
  }

  params.set("range", options.range ?? "day");

  const query = params.toString();
  const res = await apiFetch(`/metrics/time${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function signup(email: string, password: string): Promise<AuthResponse> {
  const res = await apiFetch("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function logout(): Promise<void> {
  const res = await apiFetch("/auth/logout", {
    method: "POST",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const res = await apiFetch("/auth/me", {
    cache: "no-store",
  });

  if (res.status === 401) {
    return null;
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function fetchAuthConfig(): Promise<AuthConfigResponse> {
  const res = await apiFetch("/auth/config", {
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function fetchLLMCatalog(): Promise<LLMCatalogResponse> {
  const res = await apiFetch("/llm/catalog", {
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function fetchHistory(token: string): Promise<HistoryResponse> {
  const res = await apiFetch("/history", {
    headers: authHeaders(token),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function fetchRunSession(sessionId: number, token: string): Promise<RunSessionState> {
  const res = await apiFetch(`/session/${sessionId}`, {
    headers: authHeaders(token),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function clearRunSession(sessionId: number, token: string): Promise<RunSessionState> {
  const res = await apiFetch(`/session/${sessionId}/clear`, {
    method: "POST",
    headers: authHeaders(token),
    body: "{}",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function explainRun(runId: number, token: string, llm?: LLMRequestOptions): Promise<RunExplanation> {
  const res = await apiFetch(`/explain/${runId}`, {
    method: "POST",
    headers: authHeaders(token, llm),
    body: "{}",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

// ── Sharing ──────────────────────────────────────────────

export interface ShareRunResponse {
  share_token: string;
  is_public: boolean;
  expires_at: string | null;
}

export interface SharedRun {
  id: number;
  project: string;
  input: string;
  output: string;
  memory: RunMemoryEntry[];
  timeline: RunTimelineEntry[];
  latency: number;
  confidence: number;
  timestamp: string | null;
}

export async function shareRun(
  runId: number,
  token: string,
  expiresInHours?: number,
): Promise<ShareRunResponse> {
  const body: Record<string, unknown> = {};
  if (expiresInHours !== undefined) {
    body.expires_in_hours = expiresInHours;
  }

  const res = await apiFetch(`/run/${runId}/share`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}

export async function unshareRun(runId: number, token: string): Promise<void> {
  const res = await apiFetch(`/run/${runId}/share`, {
    method: "DELETE",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
}

export async function fetchSharedRun(shareToken: string): Promise<SharedRun> {
  const res = await apiFetch(`/shared/${encodeURIComponent(shareToken)}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  return res.json();
}


// ── Streaming ────────────────────────────────────────────

export interface StepEvent {
  step: string;
  status: "running" | "done" | "error";
  error?: string;
}

export interface StreamCallbacks {
  onOpen?: () => void;
  onToken: (token: string) => void;
  onStep?: (event: StepEvent) => void;
  onDone: (meta: {
    latency: number;
    success: boolean;
    confidence: number;
    sessionId: number | null;
    sessionMemory: string[];
    usedSessionContext: boolean;
  }) => void;
  onError: (error: string) => void;
}

function dispatchStreamEvent(rawEvent: string, callbacks: StreamCallbacks): "continue" | "done" | "error" {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of rawEvent.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  const payload = dataLines.join("\n");
  if (!payload) {
    return "continue";
  }

  if (eventName === "step") {
    try {
      const data = JSON.parse(payload);
      callbacks.onStep?.({
        step: data.step,
        status: data.status,
        error: typeof data.error === "string" ? data.error : undefined,
      });
    } catch {
      // Ignore malformed step frames.
    }
    return "continue";
  }

  if (eventName === "done") {
    try {
      const data = JSON.parse(payload);
      callbacks.onDone({
        latency: data.latency ?? 0,
        success: data.success ?? true,
        confidence: data.confidence ?? 0,
        sessionId: data.session_id ?? null,
        sessionMemory: Array.isArray(data.session_memory)
          ? data.session_memory.filter((entry: unknown): entry is string => typeof entry === "string")
          : [],
        usedSessionContext: data.used_session_context === true,
      });
    } catch {
      callbacks.onDone({
        latency: 0,
        success: true,
        confidence: 0,
        sessionId: null,
        sessionMemory: [],
        usedSessionContext: false,
      });
    }
    return "done";
  }

  if (eventName === "error") {
    callbacks.onError(parseErrorMessage(payload, "Stream error"));
    return "error";
  }

  if (eventName === "output") {
    // The backend emits a single ``event: output`` frame carrying the full
    // completed output string.  This is not token-level streaming — the
    // project has already finished generating by the time this frame is
    // sent — but it lets the UI show the output as soon as it arrives and
    // is honest about the single-shot nature of the payload.
    try {
      const data = JSON.parse(payload);
      if (typeof data.output === "string") {
        callbacks.onToken(data.output);
      }
    } catch {
      // Ignore malformed output frames.
    }
    return "continue";
  }

  try {
    const data = JSON.parse(payload);
    if (typeof data.token === "string") {
      callbacks.onToken(data.token);
    }
  } catch {
    // Ignore malformed token frames.
  }

  return "continue";
}

/**
 * Connect to the SSE stream endpoint and call back on each chunk.
 * Returns an abort function to disconnect early.
 */
export function streamProject(
  projectName: string,
  input: string,
  callbacks: StreamCallbacks,
  token?: string,
  llm?: LLMRequestOptions,
  sessionId?: number | null,
): () => void {
  const params = new URLSearchParams({ input });
  if (sessionId !== undefined && sessionId !== null) {
    params.set("session_id", String(sessionId));
  }
  const path = `/stream/${encodeURIComponent(projectName)}?${params}`;

  const controller = new AbortController();
  let terminated = false;

  void (async () => {
    try {
      const headers: Record<string, string> = {
        Accept: "text/event-stream",
      };
      if (token && token !== AUTH_SESSION_MARKER) {
        headers.Authorization = `Bearer ${token}`;
      }
      if (llm?.apiKey) {
        headers["X-API-Key"] = llm.apiKey;
      }
      if (llm?.provider) {
        headers["X-LLM-Provider"] = llm.provider;
      }
      if (llm?.model) {
        headers["X-LLM-Model"] = llm.model;
      }

      const res = await apiFetch(path, {
        method: "GET",
        headers,
        cache: "no-store",
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        callbacks.onError(formatRunError(res.status, res.statusText, text));
        terminated = true;
        return;
      }

      if (!res.body) {
        callbacks.onError("Empty stream response.");
        terminated = true;
        return;
      }

      callbacks.onOpen?.();

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!terminated) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const rawEvent = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);

          const result = dispatchStreamEvent(rawEvent, callbacks);
          if (result !== "continue") {
            terminated = true;
            break;
          }

          boundary = buffer.indexOf("\n\n");
        }
      }

      if (!terminated) {
        buffer += decoder.decode();
        if (buffer.trim()) {
          dispatchStreamEvent(buffer, callbacks);
        }
      }
    } catch (error) {
      if (terminated) {
        return;
      }
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      callbacks.onError(error instanceof Error ? error.message : "Stream disconnected");
    }
  })();

  return () => {
    terminated = true;
    controller.abort();
  };
}
