"""Execution entry point for the Generative UI Builder."""

import json
import os

from app.spec_generator import generate_spec
from app.validator import validate_spec
from app.code_generator import generate_files
from app.fixer import fix_code
from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

MAX_FIX_ATTEMPTS = 1


def build(prompt: str) -> dict:
    """Run the full pipeline: generate spec, validate, generate code, fix if needed."""

    # 1. Generate UI spec
    print(f"\n[1/5] Generating UI spec from prompt...")
    emit_step("spec", "running")
    spec = generate_spec(prompt)
    emit_step("spec", "done")

    print("\n--- Generated JSON Spec ---")
    print(json.dumps(spec, indent=2))
    print("---\n")

    # 2. Validate spec
    print("[2/5] Validating spec...")
    emit_step("validator", "running")
    if not validate_spec(spec):
        emit_step("validator", "done")
        print("ERROR: Spec validation failed.")
        return {"success": False, "error": "Generated spec failed validation."}
    emit_step("validator", "done")
    print("Spec is valid.\n")

    # 3. Generate React code
    print("[3/5] Generating React code...")
    emit_step("codegen", "running")
    files = generate_files(spec)
    emit_step("codegen", "done")
    app_code = files.get("App.jsx", "")

    # 4. Fix loop (if App.jsx has issues)
    if "export default function" in app_code and "import React" in app_code:
        print("[4/5] No fixes needed.\n")
    else:
        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            print(f"[4/5] Fixing code (attempt {attempt}/{MAX_FIX_ATTEMPTS})...")
            emit_step("repair", "running")
            app_code = fix_code(app_code, "Generated code is missing required React structure.")
            files["App.jsx"] = app_code
            emit_step("repair", "done")
            if "export default function" in app_code and "import React" in app_code:
                break

    # 5. Save output
    print("[5/5] Saving output...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved_paths: list[str] = []
    for filename, content in files.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        saved_paths.append(os.path.abspath(filepath))

    print(f"\nOutput saved to: {os.path.abspath(OUTPUT_DIR)}/")
    for path in saved_paths:
        print(f"  {path}")
    return {"success": True, "paths": saved_paths, "spec": spec, "files": files}


def run(input: str, api_key: str) -> dict:
    """Run the UI generation pipeline and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        return build(input)
    finally:
        reset_byok_api_key(token)