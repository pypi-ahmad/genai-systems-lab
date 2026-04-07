"use client";

import { useEffect, useState, type ReactNode } from "react";
import { projectDetails } from "@/data/projects";
import {
  fetchMetricsTime,
  type MetricsTimeRange,
  type TimeSeriesMetricPoint,
} from "@/lib/api";
import { DismissibleTip } from "@/components/dismissible-tip";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ChartPoint = {
  label: string;
  detailLabel: string;
  latency: number | null;
  confidence: number | null;
  successRate: number | null;
  runs: number;
};

type TrendSummary = {
  label: string;
  toneClass: string;
  summary: string;
};

const projectMeta = new Map(
  projectDetails.map((project) => [project.slug, project] as const),
);

const rangeMeta: Record<MetricsTimeRange, {
  label: string;
  bucketMs: number;
  durationMs: number;
  bucketLabel: string;
}> = {
  hour: {
    label: "Last hour",
    bucketMs: 5 * 60 * 1000,
    durationMs: 60 * 60 * 1000,
    bucketLabel: "5-minute intervals",
  },
  day: {
    label: "Last day",
    bucketMs: 60 * 60 * 1000,
    durationMs: 24 * 60 * 60 * 1000,
    bucketLabel: "hourly intervals",
  },
  week: {
    label: "Last week",
    bucketMs: 24 * 60 * 60 * 1000,
    durationMs: 7 * 24 * 60 * 60 * 1000,
    bucketLabel: "daily intervals",
  },
};

const rangeOptions: Array<{ value: MetricsTimeRange; label: string }> = [
  { value: "hour", label: "Last hour" },
  { value: "day", label: "Last day" },
  { value: "week", label: "Last week" },
];

const tooltipStyle = {
  borderRadius: "16px",
  border: "1px solid var(--chart-tooltip-border)",
  backgroundColor: "var(--chart-tooltip-bg)",
  boxShadow: "var(--chart-tooltip-shadow)",
};

function formatLatency(value: number) {
  return `${Math.round(value)} ms`;
}

function formatConfidence(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatRate(value: number) {
  return `${value.toFixed(1)}%`;
}

function fallbackProjectLabel(project: string) {
  return project
    .replace(/^(genai-|crew-|lg-)/, "")
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function projectLabel(project: string) {
  return projectMeta.get(project)?.name ?? fallbackProjectLabel(project);
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function bucketLabels(timestamp: number, range: MetricsTimeRange) {
  const date = new Date(timestamp);
  if (range === "hour") {
    return {
      axis: date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
      detail: date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }),
    };
  }

  if (range === "day") {
    return {
      axis: date.toLocaleTimeString([], { hour: "numeric" }),
      detail: date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
      }),
    };
  }

  return {
    axis: date.toLocaleDateString([], { month: "short", day: "numeric" }),
    detail: date.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" }),
  };
}

function average(values: Array<number | null>) {
  const numericValues = values.filter(
    (value): value is number => typeof value === "number" && Number.isFinite(value),
  );

  if (numericValues.length === 0) {
    return null;
  }

  return numericValues.reduce((total, value) => total + value, 0) / numericValues.length;
}

function describeLatencyDelta(delta: number) {
  if (Math.abs(delta) < 1) {
    return "latency is flat";
  }

  if (delta < 0) {
    return `${Math.abs(delta).toFixed(0)} ms faster`;
  }

  return `${delta.toFixed(0)} ms slower`;
}

function describePointDelta(delta: number, label: string) {
  if (Math.abs(delta) < 0.1) {
    return `${label} is flat`;
  }

  return `${delta > 0 ? "+" : ""}${delta.toFixed(1)} points ${label}`;
}

function buildChartSeries(points: TimeSeriesMetricPoint[], range: MetricsTimeRange): ChartPoint[] {
  const config = rangeMeta[range];
  const grouped = new Map<number, {
    latencyTotal: number;
    confidenceTotal: number;
    successCount: number;
    runs: number;
  }>();

  for (const point of points) {
    const timestamp = new Date(point.timestamp).getTime();
    if (Number.isNaN(timestamp)) {
      continue;
    }

    const bucket = Math.floor(timestamp / config.bucketMs) * config.bucketMs;
    const current = grouped.get(bucket) ?? {
      latencyTotal: 0,
      confidenceTotal: 0,
      successCount: 0,
      runs: 0,
    };

    current.latencyTotal += point.latency;
    current.confidenceTotal += point.confidence;
    current.successCount += point.success ? 1 : 0;
    current.runs += 1;
    grouped.set(bucket, current);
  }

  const now = Date.now();
  const firstBucket = Math.floor((now - config.durationMs) / config.bucketMs) * config.bucketMs;
  const lastBucket = Math.floor(now / config.bucketMs) * config.bucketMs;
  const series: ChartPoint[] = [];

  for (let bucket = firstBucket; bucket <= lastBucket; bucket += config.bucketMs) {
    const labels = bucketLabels(bucket, range);
    const current = grouped.get(bucket);

    series.push({
      label: labels.axis,
      detailLabel: labels.detail,
      latency: current ? current.latencyTotal / current.runs : null,
      confidence: current ? current.confidenceTotal / current.runs : null,
      successRate: current ? (current.successCount / current.runs) * 100 : null,
      runs: current?.runs ?? 0,
    });
  }

  return series;
}

function buildTrendSummary(series: ChartPoint[]): TrendSummary {
  const populated = series.filter((point) => point.runs > 0);
  if (populated.length < 2) {
    return {
      label: "Insufficient data",
      toneClass: "surface-pill text-[var(--muted)]",
      summary: "Run more requests in this window to see whether the system is improving or degrading.",
    };
  }

  const sampleSize = Math.max(1, Math.floor(populated.length / 3));
  const startSlice = populated.slice(0, sampleSize);
  const endSlice = populated.slice(-sampleSize);

  const startLatency = average(startSlice.map((point) => point.latency));
  const endLatency = average(endSlice.map((point) => point.latency));
  const startConfidence = average(startSlice.map((point) => point.confidence));
  const endConfidence = average(endSlice.map((point) => point.confidence));
  const startSuccess = average(startSlice.map((point) => point.successRate));
  const endSuccess = average(endSlice.map((point) => point.successRate));

  const latencyDelta = startLatency !== null && endLatency !== null ? endLatency - startLatency : 0;
  const confidenceDelta = startConfidence !== null && endConfidence !== null ? (endConfidence - startConfidence) * 100 : 0;
  const successDelta = startSuccess !== null && endSuccess !== null ? endSuccess - startSuccess : 0;

  let score = 0;
  if (latencyDelta <= -40) {
    score += 1;
  } else if (latencyDelta >= 40) {
    score -= 1;
  }

  if (confidenceDelta >= 3) {
    score += 1;
  } else if (confidenceDelta <= -3) {
    score -= 1;
  }

  if (successDelta >= 3) {
    score += 1;
  } else if (successDelta <= -3) {
    score -= 1;
  }

  const summary = `${describeLatencyDelta(latencyDelta)}, ${describePointDelta(confidenceDelta, "confidence")}, and ${describePointDelta(successDelta, "success rate")} versus the start of the window.`;

  if (score >= 2) {
    return {
      label: "Improving",
      toneClass: "status-positive",
      summary,
    };
  }

  if (score <= -2) {
    return {
      label: "Degrading",
      toneClass: "status-error",
      summary,
    };
  }

  return {
    label: "Stable",
    toneClass: "surface-pill text-[var(--foreground)]",
    summary: "Recent runs are mostly holding steady with no strong directional shift across latency, confidence, and success rate.",
  };
}

function StatCard({
  label,
  value,
  note,
  badge,
}: {
  label: string;
  value: string;
  note: string;
  badge?: string;
}) {
  return (
    <article className="surface-card rounded-[1.5rem] p-6 sm:p-7">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
          {label}
        </p>
        {badge ? (
          <span className="surface-pill rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
            {badge}
          </span>
        ) : null}
      </div>
      <p className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-5xl">
        {value}
      </p>
      <p className="copy-body mt-3 text-sm">{note}</p>
    </article>
  );
}

function ChartCard({
  eyebrow,
  title,
  description,
  children,
  className = "",
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <article className={`surface-card rounded-[1.5rem] p-6 sm:p-7 ${className}`.trim()}>
      <div className="section-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="heading-card text-xl text-[var(--foreground)]">{title}</h2>
        <p className="copy-body text-sm">{description}</p>
      </div>
      <div className="mt-6">{children}</div>
    </article>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <section className="py-16">
      <div className="surface-card rounded-[1.5rem] p-6 sm:p-8">
        <p className="eyebrow">Performance Over Time</p>
        <h2 className="heading-section mt-3 text-3xl text-[var(--foreground)]">
          No metrics match this filter yet
        </h2>
        <p className="copy-body mt-4 max-w-2xl text-sm">{message}</p>
      </div>
    </section>
  );
}

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportJSON(data: TimeSeriesMetricPoint[]) {
  downloadBlob(JSON.stringify(data, null, 2), "metrics.json", "application/json");
}

function exportCSV(data: TimeSeriesMetricPoint[]) {
  const header = "timestamp,latency,confidence,success";
  const rows = data.map((p) => `${p.timestamp},${p.latency},${p.confidence},${p.success}`);
  downloadBlob([header, ...rows].join("\n"), "metrics.csv", "text/csv");
}

export default function MetricsPage() {
  const [selectedProject, setSelectedProject] = useState("all");
  const [range, setRange] = useState<MetricsTimeRange>("day");
  const [points, setPoints] = useState<TimeSeriesMetricPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetchMetricsTime({
      project: selectedProject === "all" ? undefined : selectedProject,
      range,
    })
      .then((response) => {
        if (!cancelled) {
          setPoints(response);
        }
      })
      .catch((fetchError) => {
        if (!cancelled) {
          setError(fetchError instanceof Error ? fetchError.message : "Failed to load metrics.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [range, selectedProject]);

  if (loading) {
    return (
      <section className="flex min-h-[50vh] items-center justify-center py-16">
        <div className="surface-card flex items-center gap-3 rounded-full px-5 py-3 text-sm text-[var(--muted)]">
          <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent-solid)]" />
          Loading run metrics.
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="space-y-8 py-16">
        <div className="title-stack">
          <p className="eyebrow">Performance Over Time</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Historical run metrics are unavailable right now.
          </h1>
          <p className="copy-body max-w-2xl text-sm sm:text-base">
            Check your connection and try again shortly.
          </p>
        </div>

        <div className="surface-card error-panel rounded-[1.5rem] p-6 sm:p-8">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--danger-text)]">
            Unable to load metrics
          </p>
          <p className="mt-4 text-base leading-8 text-[var(--danger-text-soft)]">{error}</p>
        </div>
      </section>
    );
  }

  if (points.length === 0) {
    const projectDescription = selectedProject === "all"
      ? "the selected time range"
      : `${projectLabel(selectedProject)} in the selected time range`;

    return (
      <EmptyState message={`No metrics were found for ${projectDescription}. Run a few projects and this view will populate automatically.`} />
    );
  }

  const chartSeries = buildChartSeries(points, range);
  const populatedSeries = chartSeries.filter((point) => point.runs > 0);
  const averageLatency = average(populatedSeries.map((point) => point.latency));
  const averageConfidence = average(populatedSeries.map((point) => point.confidence));
  const averageSuccess = average(populatedSeries.map((point) => point.successRate));
  const latestRun = points[points.length - 1];
  const trend = buildTrendSummary(chartSeries);
  const activeProjectLabel = selectedProject === "all" ? "All systems" : projectLabel(selectedProject);

  return (
    <div className="space-y-0">
      <DismissibleTip
        storageKey="tip-metrics-intro"
        text="Metrics are computed from your playground runs. Pick a project and time range to see latency, confidence, and success trends."
        className="mb-4 mt-16"
      />
      <section className="section-accent grid gap-8 py-16 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
        <div className="title-stack">
          <p className="eyebrow">Performance Over Time</p>
          <h1 className="heading-display text-4xl sm:text-5xl">
            Track whether the system is improving, holding, or slipping.
          </h1>
          <p className="copy-lead max-w-2xl text-base sm:text-lg">
            Run metrics are grouped by {rangeMeta[range].bucketLabel} so latency, confidence, and success rate reveal actual direction over time.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${trend.toneClass}`}>
              {trend.label}
            </span>
            <span className="surface-pill rounded-full px-3 py-1 text-xs text-[var(--muted)]">
              {activeProjectLabel}
            </span>
          </div>
        </div>

        <div className="surface-card rounded-[1.5rem] p-6 sm:p-7">
          <p className="eyebrow">Filters</p>
          <div className="mt-5 grid gap-5">
            <label>
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                Project
              </span>
              <select
                value={selectedProject}
                onChange={(event) => {
                  setLoading(true);
                  setError(null);
                  setSelectedProject(event.target.value);
                }}
                className="input-shell mt-2 w-full rounded-[1rem] px-4 py-3 text-sm"
              >
                <option value="all">All projects</option>
                {projectDetails.map((project) => (
                  <option key={project.slug} value={project.slug}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>

            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                Time range
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {rangeOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      setLoading(true);
                      setError(null);
                      setRange(option.value);
                    }}
                    className={`button-base button-sm button-pill ${range === option.value ? "button-primary" : "button-secondary"}`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="surface-panel mt-6 rounded-[1.25rem] px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                Trend summary
              </p>
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${trend.toneClass}`}>
                {trend.label}
              </span>
            </div>
            <p className="copy-body mt-3 text-sm">{trend.summary}</p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => exportJSON(points)} className="button-base button-secondary button-sm button-pill">
              Export JSON
            </button>
            <button type="button" onClick={() => exportCSV(points)} className="button-base button-secondary button-sm button-pill">
              Export CSV
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-6 py-16 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Runs Analyzed"
          value={points.length.toLocaleString()}
          note={latestRun ? `Latest saved run at ${formatTimestamp(latestRun.timestamp)}.` : "No saved runs in this window yet."}
          badge={rangeMeta[range].label}
        />
        <StatCard
          label="Average Latency"
          value={averageLatency !== null ? formatLatency(averageLatency) : "--"}
          note="Average completion time across the visible intervals. Lower is better."
        />
        <StatCard
          label="Average Confidence"
          value={averageConfidence !== null ? formatConfidence(averageConfidence) : "--"}
          note="Mean confidence across runs in the selected time range."
        />
        <StatCard
          label="Success Rate"
          value={averageSuccess !== null ? formatRate(averageSuccess) : "--"}
          note="Share of runs that completed successfully in the selected window."
        />
      </section>

      <div className="section-divider" />

      <section className="space-y-6 py-16">
        <div className="section-heading">
          <p className="eyebrow">Charts</p>
          <h2 className="heading-section text-3xl text-[var(--foreground)]">
            Clean views of the three metrics that matter most.
          </h2>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <ChartCard
            eyebrow="Latency"
            title="Latency over time"
            description="Average latency per interval. A downward slope means the system is getting faster."
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartSeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 8" vertical={false} stroke="var(--chart-grid)" />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  fontSize={12}
                  minTickGap={28}
                  tick={{ fill: "var(--muted)" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  width={56}
                  fontSize={12}
                  tick={{ fill: "var(--muted)" }}
                  tickFormatter={(value: number) => `${Math.round(value)} ms`}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.detailLabel ?? ""}
                  formatter={(value) => {
                    const numericValue = typeof value === "number" ? value : Number(value);
                    return [formatLatency(numericValue), "Latency"];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="var(--accent-solid)"
                  strokeWidth={3}
                  dot={false}
                  connectNulls={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            eyebrow="Confidence"
            title="Confidence over time"
            description="Average confidence per interval. A rising line suggests responses are becoming more reliable."
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartSeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 8" vertical={false} stroke="var(--chart-grid)" />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  fontSize={12}
                  minTickGap={28}
                  tick={{ fill: "var(--muted)" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  width={52}
                  fontSize={12}
                  tick={{ fill: "var(--muted)" }}
                  domain={[0, 1]}
                  tickFormatter={(value: number) => `${Math.round(value * 100)}%`}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.detailLabel ?? ""}
                  formatter={(value) => {
                    const numericValue = typeof value === "number" ? value : Number(value);
                    return [formatConfidence(numericValue), "Confidence"];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="var(--done-text)"
                  strokeWidth={3}
                  dot={false}
                  connectNulls={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            eyebrow="Reliability"
            title="Success rate over time"
            description="Success percentage per interval. This makes reliability drift obvious without scanning individual runs."
            className="xl:col-span-2"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartSeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 8" vertical={false} stroke="var(--chart-grid)" />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  fontSize={12}
                  minTickGap={28}
                  tick={{ fill: "var(--muted)" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  width={52}
                  fontSize={12}
                  tick={{ fill: "var(--muted)" }}
                  domain={[0, 100]}
                  tickFormatter={(value: number) => `${Math.round(value)}%`}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.detailLabel ?? ""}
                  formatter={(value) => {
                    const numericValue = typeof value === "number" ? value : Number(value);
                    return [formatRate(numericValue), "Success rate"];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="successRate"
                  stroke="var(--success-dot)"
                  strokeWidth={3}
                  dot={false}
                  connectNulls={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>
    </div>
  );
}