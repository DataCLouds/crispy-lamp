---
name: Task
about: Chore, refactor, or non-feature work (CI, tooling, docs, migrations)
title: "[Task] "
labels: task
assignees: ''
---

## What

<!-- One sentence. Example:
"Add Flask-Migrate and set up the initial migration." -->

## Why

<!-- Example:
"Models will start changing frequently in V1 - need a safe way
to evolve the schema instead of hand-editing the database." -->

## Type

```text
[ ] Tooling / dependency
[ ] CI / GitHub Actions
[ ] Docs / README
[ ] Refactor (no behavior change)
[ ] Config / environment
```

## Acceptance criteria

<!-- Example:
- [ ] `uv add flask-migrate` committed to pyproject.toml / uv.lock
- [ ] `migrations/` folder created and committed
- [ ] README updated with the migration workflow
- [ ] uv run pytest still passes
-->

- [ ]
- [ ]

## Checks before closing

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Suggested branch name

```text
bugfix/<yourname>/<short-slug>   # if it's a fix
feature/<yourname>/<short-slug>  # if it's new tooling/setup
```
