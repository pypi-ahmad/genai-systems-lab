# Tasks

## Define UI JSON Schema

- Define the canonical JSON schema for the UI spec in `app/templates/`.
- Include required top-level fields: `name`, `description`, `tree`, `props`, `styles`.
- Define the tree node structure with `type`, `props`, `children`, `style`, and `condition`.
- Add allowed component types and prop type constraints.
- Add a schema loading utility that downstream stages can import.

## Generate UI Spec

- Create the spec generation interface in `app/spec_generator.py`.
- Build a system prompt that instructs the model to output strict JSON matching the schema.
- Accept a user prompt and return a parsed JSON UI spec.
- Use `gemini-3.1-pro-preview` for spec generation.
- Extract raw JSON from the model response, handling markdown fences if present.

## Validate Spec

- Create the validation interface in `app/validator.py`.
- Validate a JSON UI spec against the canonical schema.
- Check structural rules: required fields, allowed types, correct nesting.
- Check semantic rules: duplicate keys, orphan references, conflicting constraints.
- Return a list of typed errors with JSON paths for targeted fixing.

## Build Code Generator

- Create the code generation interface in `app/code_generator.py`.
- Walk the validated spec tree and map each node to a React component.
- Emit functional components with named exports and standard imports.
- Apply style directives from the spec as inline styles or className assignments.
- Write generated files to the `output/` directory.

## Implement Fix Loop

- Create the fixer loop interface in `app/fixer.py`.
- Accept a spec or code string along with a list of validation errors.
- Send the current output and errors to `gemini-3-flash-preview` for correction.
- Re-validate after each fix attempt and loop until valid or iteration limit is reached.
- Set a configurable maximum iteration count with a default of 3.
- Return the fixed output and a summary of iterations and remaining issues.

## Save Output Files

- Write final React component files to `output/` with correct naming from the spec.
- Create a generation summary including component name, file paths, and iteration count.
- Handle file overwrites and directory creation for the output path.
- Log any unresolved warnings from the fixer loop in the summary.

