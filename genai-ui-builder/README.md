# Generative UI Builder

## Overview

A prompt-to-UI workflow that converts natural-language descriptions into structured UI specs, validates them, generates React code, and optionally repairs invalid outputs. The project focuses on deterministic code generation from a constrained intermediate format.

## System Flow

A user prompt is converted into a JSON UI specification, the spec is validated against allowed component types and structure, React files are generated, and a lightweight fix loop can repair missing or invalid output shapes.

```text
Prompt -> Spec Generator -> Validator -> Code Generator -> Fix Loop -> React Files
```

## Architecture

The codebase separates spec generation, validation, code generation, repair, and preview so the UI generation pipeline remains inspectable at every stage.

| Module | Responsibility |
|--------|----------------|
| app/spec_generator.py | Creates the structured UI spec from a natural-language prompt. |
| app/validator.py | Checks the generated spec against the allowed schema. |
| app/code_generator.py | Converts validated specs into React component files. |
| app/fixer.py | Repairs invalid generated code with a bounded retry loop. |
| app/preview.py | Serves a lightweight browser preview for generated UI output. |

## Features

- Structured JSON intermediate representation for predictable generation.
- Schema-based validation before code output is accepted.
- React file generation with optional preview workflow.
- Bounded repair loop for malformed or incomplete code output.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/generative-ui-builder/run \
  -H "Content-Type: application/json" \
  -d '{"input": "A dashboard with a sidebar, header, and data table"}'
```

## Evaluation

```text
POST /eval/generative-ui-builder
```

Primary metrics: spec validity rate, code generation success, component coverage, latency, and failure rate.
