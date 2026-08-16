# Pull Request

## What this PR does

<!-- Clear, one-paragraph description of the change and why it is needed. -->

## Type of change

- [ ] Bug fix
- [ ] New AI project (new `run()` module)
- [ ] Platform / infrastructure feature
- [ ] Documentation update
- [ ] Dependency update
- [ ] Refactor (no behavior change)
- [ ] Other: 

## Related issue

Closes #

## Verification

- [ ] `uv run pytest` passes locally
- [ ] `uv run ruff check .` reports no errors
- [ ] `uv run ruff format --check .` reports no errors
- [ ] New / changed behavior is covered by a test
- [ ] `uv.lock` is updated if `pyproject.toml` changed (`uv lock`)

## Checklist

- [ ] This PR targets `main`
- [ ] The commit messages explain *why*, not just *what*
- [ ] No API keys, JWT secrets, or credentials are included in any changed file
- [ ] `uv.lock` is committed alongside any `pyproject.toml` changes

## Notes for the reviewer

<!-- Anything that needs extra attention, known limitations, or follow-up issues to open. -->
