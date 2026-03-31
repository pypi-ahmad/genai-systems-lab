# Architecture

## Overview

The Generative UI Builder converts natural-language prompts into production-ready React component code through a structured, multi-stage pipeline. A strict JSON UI spec acts as the intermediate representation between intent and code, giving every downstream stage a deterministic contract to work against.

Primary flow:

`Prompt → JSON UI Spec → React Code → Validate → Fix → Final Output`

## Core Components

### Spec Generator

- Accepts a free-form user prompt describing the desired UI.
- Produces a structured JSON UI spec that conforms to a predefined schema.
- The spec captures layout hierarchy, component types, props, styling directives, and data bindings.
- All downstream stages consume this spec—never the raw prompt.

### Validator

- Validates the JSON UI spec against the canonical JSON schema before code generation begins.
- Checks structural correctness: required fields, allowed component types, prop types, nesting rules.
- Checks semantic correctness: duplicate keys, orphan references, conflicting layout constraints.
- Returns a list of typed validation errors with paths so the Fixer Loop or Spec Generator can act on them.

### Code Generator

- Converts a validated JSON UI spec into React component source code.
- Maps each spec node to a React component with the correct props, children, and styling.
- Produces self-contained, importable component files with standard project conventions (functional components, named exports).
- Outputs code to the `output/` directory alongside any supporting files.

### Fixer Loop

- Receives validation errors or code-level issues and attempts automated repair.
- Operates iteratively: fix → re-validate → fix again, up to a configurable maximum iteration count.
- Targets both spec-level and code-level problems (malformed JSON, missing imports, type mismatches).
- Exits early when the output passes validation or the iteration limit is reached, whichever comes first.

## JSON UI Spec Schema

The spec is the single source of truth between generation and code output. It must conform to a strict JSON schema.

Required top-level fields:

| Field         | Type     | Description                                      |
|---------------|----------|--------------------------------------------------|
| `name`        | string   | Component name (PascalCase)                      |
| `description` | string   | Brief summary of the component's purpose         |
| `tree`        | object   | Root node of the component tree                  |
| `props`       | array    | Top-level props accepted by the component        |
| `styles`      | object   | Global or shared style directives                |

Each node in `tree` contains:

| Field       | Type     | Description                                      |
|-------------|----------|--------------------------------------------------|
| `type`      | string   | Component or HTML element type                   |
| `props`     | object   | Key-value prop assignments                       |
| `children`  | array    | Nested child nodes                               |
| `style`     | object   | Inline style overrides                           |
| `condition` | string   | Optional render condition expression             |

The schema is enforced at two points: after spec generation and after each fixer iteration. No stage may pass a spec that does not validate.

## System Flow

### 1. Prompt Intake

The system receives the user's natural-language prompt describing the UI to build. The prompt is normalized and forwarded to the Spec Generator.

### 2. Spec Generation

The Spec Generator calls the LLM to produce a JSON UI spec from the prompt. The response is parsed, and raw JSON is extracted from the model output.

### 3. Spec Validation

The Validator checks the generated spec against the JSON schema. If validation passes, the spec moves to code generation. If it fails, the errors are routed to the Fixer Loop.

### 4. Spec Fixing (if needed)

The Fixer Loop sends the current spec and its validation errors back to the LLM, requesting a corrected version. The corrected spec is re-validated. This repeats until the spec is valid or the iteration limit is hit.

### 5. Code Generation

The Code Generator walks the validated spec tree and emits React component source code. Output files are written to the `output/` directory.

### 6. Code Validation

The generated code is checked for structural issues: syntax errors, missing imports, undefined references. If issues are found, they enter the Fixer Loop for code-level repair.

### 7. Code Fixing (if needed)

The Fixer Loop patches the generated code using LLM-assisted corrections, re-validates after each pass, and exits when the code is clean or the limit is reached.

### 8. Final Output

The validated code is written to `output/` as the final deliverable. A summary of the generation run (component name, file paths, iteration count, any unresolved warnings) is returned to the caller.

## Model Usage

### `gemini-3.1-pro-preview`

Use for spec generation—the most reasoning-intensive stage in the pipeline.

Recommended responsibilities:

- Spec Generator: converting free-form prompts into structured JSON UI specs.
- Complex spec-level fixes that require understanding component relationships.

### `gemini-3-flash-preview`

Use for faster, lower-cost operations where the task is well-constrained.

Recommended responsibilities:

- Fixer Loop: targeted repairs given explicit error messages and paths.
- Code-level refinements: import corrections, style adjustments, minor rewrites.

This split keeps the high-reasoning prompt-to-spec translation on the stronger model while using the faster model for iterative, feedback-driven corrections.

## Production-Oriented Design Notes

- **Strict schema enforcement.** The JSON UI spec schema is the system's contract. Every transition between stages must pass validation. No stage may silently drop or ignore schema violations.
- **Iteration limits.** The Fixer Loop must have a hard cap on iterations (recommended default: 3). Unbounded loops risk cost blowouts and infinite retries on fundamentally broken specs.
- **Deterministic outputs.** Given the same spec, the Code Generator should produce identical code. Non-determinism should be confined to the LLM-powered stages (Spec Generator, Fixer Loop).
- **Structured error reporting.** Every validation failure should include the JSON path, expected type or value, and actual value. This enables targeted fixes rather than full regeneration.
- **Template support.** The `templates/` directory holds base component templates and code scaffolds. The Code Generator should use these as starting points rather than generating everything from scratch.
- **Logging and traceability.** Each pipeline run should log the original prompt, generated spec, validation results, fixer iterations, and final output. This supports debugging and quality auditing.
- **Graceful degradation.** If the Fixer Loop exhausts its iterations without a valid result, the system should return partial output with a clear error summary—not silently fail.

## High-Level Architecture Summary

The system is organized as a linear pipeline with a feedback loop. The Spec Generator translates user intent into a strict JSON UI spec. The Validator enforces schema compliance. The Code Generator produces React components from the spec. The Fixer Loop closes the gap when any stage produces invalid output. Two model tiers split work by complexity: the stronger model handles open-ended generation, and the faster model handles constrained repairs. The result is a predictable, auditable pipeline that turns natural-language UI descriptions into deployable component code.