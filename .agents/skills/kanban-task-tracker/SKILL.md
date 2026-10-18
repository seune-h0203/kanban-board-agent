---
name: kanban-task-tracker
description: Register and update Codex coding tasks in the team's existing Kanban board through the Assignment 7 Typer CLI and FastAPI. Use when Codex starts, progresses, completes, or is blocked on work and should record actual status in a shared board without duplicate cards.
---

# Kanban task tracking for Codex

Use the project's real existing board, never generate a new shared database, seed remote records, or guess IDs. This workflow writes team-visible cards; do not claim success before API persistence is verified.

## Preflight

1. Confirm the FastAPI endpoint is reachable (`python -m app.cli health`) and this project provides `app/cli.py`.
2. Obtain `TEAM_TODO_ACTOR_ID`, `TEAM_TODO_API_KEY`, `KANBAN_BOARD_ID`, and the relevant workflow column UUIDs from the team's configuration. Do not print secret environment variables or pass the key on the command line. If these values are missing, discover the real IDs with `python -m app.cli --json kanban boards` and `python -m app.cli --json kanban columns BOARD_ID` after authenticating; if still missing, stop and report why the task was **not** recorded.
3. Verify membership and editor/owner permission with `python -m app.cli --json kanban members BOARD_ID`. A viewer must not attempt a write.
4. Use the same stable `--work-key` each time the same work item progresses. Good: `assignment7/cli-integration`; bad: a random or timestamp-based key.

## Record Codex work (actual CLI + read-back)

From the repository root run the Typer CLI. For a NEW work item, use a stable `--work-key` and the actual To Do column:

```bash
python -m app.cli --json kanban register BOARD_ID --column-id TODO_COLUMN_ID --work-key assignment7/test-coverage --title "Test the board API"
```

Parse the returned JSON `id` as CARD_ID, and confirm the correct `board_id`, `created_by`, `column_id`, `title`. **Never guess a card ID.** All subsequent `register` calls reuse the same work key to avoid duplicate cards.

Before changing files, log the plan and transition to the actual Doing column:

```bash
python -m app.cli --json kanban log CARD_ID --kind plan --message "Edit tests/test_activity.py; run python -m pytest -q"
python -m app.cli --json kanban register BOARD_ID --column-id DOING_COLUMN_ID --work-key assignment7/test-coverage --title "Test the board API"
```

Perform the real work. When there are meaningful changes, append an observed update, not a fabricated result:

```bash
python -m app.cli --json kanban log CARD_ID --kind progress --message "Updated tests/test_activity.py; pending test execution"
```

After running tests, **if and only if the actual check succeeds**:

```bash
python -m app.cli --json kanban log CARD_ID --kind result --message "python -m pytest -q: 24 passed; changed tests/test_activity.py"
python -m app.cli --json kanban register BOARD_ID --column-id DONE_COLUMN_ID --work-key assignment7/test-coverage --title "Test the board API"
```

If blocked or failing, **keep the card in Doing** and write `kanban log CARD_ID --kind blocked --message "Specific failure and next action"`; never mark it Done. Activity logs append to the existing `cards.description` field and are **not** a new comments table; 5,000-character overflow returns HTTP 409. A `register --description` call can overwrite existing activity history, so **do not pass --description when updating an existing work item**.

Verify persistence with an **independent read**:

```bash
python -m app.cli --json kanban get CARD_ID
```

Compare the stored board/card/column, and confirm that description includes actual plan/progress/result (or blocked) entries. Without a successful read-back, explicitly report that persistence is unverified. `--json` and other global options belong before `kanban`.

For PowerShell on Windows, replace bash environment variable syntax with `$env:KANBAN_BOARD_ID` or use verified UUID strings directly. Never echo shared credentials.

## Safety and scope

- All writes target an **existing** member-authorized board. Do not call `python -m app.bootstrap` while configured with shared DB credentials.
- Avoid changes to other users' cards; do not clear assignees, delete cards, or overwrite an existing unrelated work item.
- A shared API key + `X-Actor-ID` is a trusted internal demo mechanism, not full individual login. Do not expose the service publicly without JWT-based user verification.
- Do not invent a completed task. Only mark done after validation. See `references/command-map.md` for command mapping and safe status handling.
