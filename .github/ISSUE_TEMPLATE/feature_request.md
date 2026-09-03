---
name: Feature request
about: Propose a new feature or enhancement
title: "[Feature] "
labels: enhancement
assignees: ''
---

## What

<!-- One or two sentences. Example:
"Add create/read/update/delete for journal entries." -->

## Which phase

<!-- Pick one -->

```text
[ ] V1 - Smart Journal
[ ] V2 - AI Emotion & Mood Analysis
[ ] V3 - Personal Insights
[ ] V4 - Voice + Multimodal
```

## Why

<!-- One sentence on why this is needed now. Example:
"Required before the dashboard can show entry counts." -->

## Acceptance criteria

<!-- Concrete, checkable outcomes. Example for journal CRUD:

- [ ] Logged-in user can create an entry with content + emotion
- [ ] User can view a list of their own entries only
- [ ] User can edit an entry they own
- [ ] User can delete an entry they own
- [ ] Attempting to edit/delete another user's entry returns 403
-->

- [ ]
- [ ]
- [ ]

## Touches

<!-- Check whatever applies, delete the rest -->

```text
[ ] New route(s) in: auth / journal / dashboard
[ ] Model change (needs a migration - see below)
[ ] Template / frontend change
[ ] Config change
```

## If this changes a model

```bash
# after editing models.py:
uv run flask db migrate -m "short description"
uv run flask db upgrade
```

## Tests to add

<!-- Example:
tests/test_journal.py
  - test_create_entry_success
  - test_create_entry_requires_login
  - test_user_cannot_edit_others_entry
-->

## Suggested branch name

```text
feature/<yourname>/<short-slug>
```
