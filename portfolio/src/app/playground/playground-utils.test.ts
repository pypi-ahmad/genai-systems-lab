import assert from "node:assert/strict";
import test from "node:test";

import {
  buildReplayNodeStatuses,
  maskApiKey,
  realtimeLifecycleState,
  summarizeInputPayload,
} from "./playground-utils";

test("maskApiKey preserves edges and caps hidden characters", () => {
  const masked = maskApiKey("abcd123456789012345678901234xyz");

  assert.equal(masked.startsWith("abcd"), true);
  assert.equal(masked.endsWith("xyz"), true);
  assert.equal(masked.slice(4, -3), "•".repeat(20));
});

test("summarizeInputPayload extracts the nested input field when present", () => {
  const summary = summarizeInputPayload('{"input":"draft a launch memo","audience":"exec"}');

  assert.equal(summary, "draft a launch memo");
});

test("summarizeInputPayload returns a fixed message for empty bodies", () => {
  assert.equal(summarizeInputPayload("   \n  "), "Empty request body.");
});

test("buildReplayNodeStatuses closes the prior running step when the next step starts", () => {
  const statuses = buildReplayNodeStatuses(
    [
      { timestamp: 0.1, step: "planner", event: "running", data: "Analyzing request" },
      { timestamp: 0.4, step: "executor", event: "running", data: "Executing plan" },
    ],
    [
      { id: "planner", label: "Planner" },
      { id: "executor", label: "Executor" },
      { id: "validator", label: "Validator" },
    ],
  );

  assert.deepEqual(statuses, {
    planner: "done",
    executor: "running",
  });
});

test("realtimeLifecycleState maps graph node statuses to lifecycle state", () => {
  const lifecycle = realtimeLifecycleState(
    "streaming",
    [
      { id: "schema-planner", label: "Schema Planner" },
      { id: "sql-executor", label: "SQL Executor" },
      { id: "result-validator", label: "Result Validator" },
      { id: "final-report", label: "Final Report" },
    ],
    {
      "schema-planner": "done",
      "sql-executor": "done",
      "result-validator": "running",
    },
  );

  assert.equal(lifecycle.activeStep, "evaluator");
  assert.deepEqual(lifecycle.completedSteps, ["planner", "executor"]);
});