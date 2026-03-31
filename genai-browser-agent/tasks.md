# Tasks

## Setup Playwright

- Add `playwright` to project dependencies.
- Run `playwright install` to download browser binaries.
- Verify Playwright launches a headless Chromium browser and navigates to a test URL.
- Confirm the browser closes cleanly after the test.

## Build Browser Controller

- Create the browser controller in `app/browser.py`.
- Add methods to launch a browser, create a new page, and close the browser.
- Add a `navigate(url)` method that goes to a URL and waits for the page to load.
- Add a `get_page_content()` method that returns the current page HTML or text.
- Add a `get_url()` method that returns the current page URL and title.
- Handle navigation timeouts and return a clear error status.

## Extract Page Content

- Create the perception module in `app/perception.py`.
- Add a method that takes raw page content from the browser controller and extracts visible text.
- Add a method that extracts interactive elements (links, buttons, inputs) with labels and identifiers.
- Compress output to stay within a configurable token limit.
- Return a structured dict with `url`, `title`, `text`, and `elements` fields.

## Define Action Space

- Create the action executor in `app/actions.py`.
- Define a fixed set of supported actions: `click`, `type`, `navigate`, `scroll`, `back`, `wait`, `done`.
- Define a structured action format: `{"action": str, "target": str, "value": str}`.
- Implement each action as a method that calls the corresponding browser controller operation.
- Add a `run(action)` dispatcher that routes an action dict to the correct method.
- Return a status dict with `success` (bool) and `message` (str) for every action.

## Implement Planner Agent

- Create the planner in `app/planner.py`.
- Build a prompt that includes the current page observation, step history, and task description.
- Call `gemini-3.1-pro-preview` with the prompt and parse the response into a structured action dict.
- If the LLM returns an unrecognized action, default to a `wait` action instead of crashing.
- Add a `done` detection path: if the planner decides the task is complete, return a `done` action.

## Implement Execution Loop

- Create the agent loop in `app/agent.py`.
- Wire together: Browser Controller → Perception → Planner → Action Executor → Memory.
- Run the Observe → Plan → Act cycle in a `while` loop.
- Break on `done` action, step limit reached, or unrecoverable error.
- Add a configurable `max_steps` parameter (default 20).
- On action failure, pass the error back to the planner for replanning before retrying.
- On repeated identical actions (same action + same URL twice), inject a loop warning into the planner prompt.

## Add Memory Tracking

- Create the memory module in `app/memory.py`.
- Store the original task description.
- Append a record for each step: step number, observation summary, planned action, execution result.
- Add a method that returns the last N steps as a formatted string for the planner prompt.
- Track visited URLs and action counts for loop detection.
- Add a method that returns the full run log for final result extraction.

