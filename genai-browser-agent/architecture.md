# Architecture

## Overview

The Autonomous Browser Agent is a loop-driven system that controls a web browser to complete user-defined tasks. It observes the current page state, plans the next action using an LLM, executes the action through Playwright, and repeats until the task is complete or a step limit is reached.

Primary loop:

`Observe → Plan → Act → Repeat`

The agent operates autonomously after receiving a task instruction. It does not require intermediate user input during execution.

## Core Components

### Browser Controller (`browser.py`)

- Manages the Playwright browser instance (launch, context, page lifecycle).
- Provides a clean interface for navigation, screenshot capture, and page content extraction.
- Handles browser-level errors (timeouts, crashes, navigation failures) and exposes recovery methods.
- Owns all direct Playwright API calls. No other component interacts with Playwright directly.

### Perception Module (`perception.py`)

- Extracts a structured representation of the current page state from the Browser Controller.
- Supports multiple extraction strategies: simplified DOM tree, visible text content, or accessible element lists.
- Filters and compresses page content to fit within LLM context limits.
- Tags interactive elements (links, buttons, inputs) with stable identifiers the Action Executor can target.

### Planner (`planner.py`)

- Receives the current page state from Perception and the task history from Memory.
- Calls the LLM to decide the single next action the agent should take.
- Returns a structured action object (action type, target element, input value) rather than free-form text.
- Detects completion conditions and signals when the task is done or unrecoverable.

### Action Executor (`actions.py`)

- Translates structured action objects from the Planner into Playwright operations.
- Supports core actions: `click`, `type`, `navigate`, `scroll`, `select`, `wait`, and `back`.
- Validates that target elements exist on the page before executing.
- Returns execution status (success or failure with reason) back to the agent loop.

### Memory (`memory.py`)

- Maintains a sequential log of all steps: observations, planned actions, execution results.
- Provides the Planner with a summarized history window to avoid exceeding context limits.
- Tracks visited URLs, repeated actions, and error counts for loop detection.
- Stores the original task description and any extracted results for the final response.

### Agent Loop (`agent.py`)

- Orchestrates the Observe → Plan → Act cycle by coordinating all components.
- Enforces a configurable maximum step limit to prevent infinite loops.
- Handles per-step error recovery: retries on transient failures, aborts on repeated errors.
- Collects the final result and returns it to the caller.

### Entry Point (`main.py`)

- Accepts the user task as input.
- Initializes the Browser Controller, Perception, Planner, Action Executor, and Memory.
- Runs the Agent Loop and returns the result.

## System Flow

### 1. Task Input

The user provides a natural-language task (e.g., "Find the price of product X on site Y"). The agent normalizes and stores it in Memory.

### 2. Browser Initialization

The Browser Controller launches a Playwright browser instance (headless by default) and opens an initial page if a starting URL is provided.

### 3. Observation

The Perception Module extracts the current page state: URL, page title, visible text, and a list of interactive elements with identifiers.

### 4. Planning

The Planner sends the current observation and step history to the LLM. The LLM returns a structured action decision: what to do next and why.

### 5. Action Execution

The Action Executor maps the planned action to a Playwright call and executes it. It waits for the page to stabilize (navigation complete, network idle) before returning.

### 6. Memory Update

The step result (observation, action, outcome) is appended to Memory. Error counts and loop-detection metrics are updated.

### 7. Loop Continuation

The agent checks termination conditions:

- **Task complete**: The Planner signals the task objective has been met.
- **Step limit reached**: The configured maximum number of steps has been exhausted.
- **Unrecoverable error**: A critical failure (browser crash, repeated action failure) that cannot be retried.

If none of these conditions are met, the loop returns to step 3.

### 8. Result Extraction

Once the loop exits, the agent compiles the final result from Memory (extracted data, final page state, or a summary of actions taken) and returns it to the caller.

## Model Usage

### `gemini-3.1-pro-preview`

Used for the Planner. All action-planning decisions go through this model.

Responsibilities:

- Interpreting the current page state against the task objective.
- Deciding the next action (click, type, navigate, done).
- Detecting task completion or failure conditions.
- Reasoning about multi-step navigation strategies.

### `gemini-3-flash-preview`

Used for lightweight, low-latency decisions that do not require deep reasoning.

Responsibilities:

- Summarizing long page content before it reaches the Planner.
- Compressing step history when it exceeds context limits.
- Extracting specific data points from page text after task completion.

This split keeps per-step latency low by reserving the heavier model for planning only.

## Constraints and Failure Handling

### Step Limit

- A configurable maximum step count (default: 20) caps every agent run.
- Prevents infinite loops from ambiguous tasks or non-converging plans.
- The agent returns a partial result with an explanation when the limit is hit.

### Action Retry

- Transient failures (element not yet visible, navigation timeout) trigger a single retry with a short wait.
- If the same action fails twice consecutively, the Planner is re-invoked with the error context to choose an alternative.

### Loop Detection

- Memory tracks the last N (action, URL) pairs.
- If the agent repeats the same action on the same page more than twice, the Planner receives a loop-detection warning and must choose a different action or abort.

### Graceful Degradation

- If the browser crashes, the agent attempts a single relaunch and resumes from the last known URL.
- If the LLM call fails, the agent retries once with exponential backoff before aborting.
- All failures are logged with step number, action attempted, and error details.

## Production-Oriented Design Notes

- All Playwright interactions are isolated in the Browser Controller so the rest of the system is testable without a real browser.
- The Perception Module's output format is stable and well-defined, allowing the Planner prompt to remain consistent across page types.
- Memory is append-only within a run. No step data is mutated after it is recorded.
- Configuration (step limit, retry count, model names, headless mode) is loaded from shared config, not hardcoded.
- Structured logging at each step (observation size, action chosen, execution time, success/failure) supports debugging and monitoring.
- The agent loop is synchronous per step. No concurrent actions are taken, which keeps browser state deterministic and reproducible.

## High-Level Architecture Summary

The system is organized around a single agent loop that coordinates five components: Browser Controller, Perception Module, Planner, Action Executor, and Memory. The Browser Controller owns all Playwright interactions. Perception extracts page state. The Planner uses an LLM to decide the next action. The Action Executor carries it out. Memory tracks everything. The loop runs until the task is complete, the step limit is reached, or an unrecoverable error occurs. The result is a focused, controllable architecture for autonomous web task execution.