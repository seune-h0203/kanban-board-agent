# Commands and validation

Find the user, board and workflow columns using `python -m app.cli --json kanban users`, `kanban boards`, `kanban members BOARD_ID`, and `kanban columns BOARD_ID`.

1. **Start**: `python -m app.cli --json kanban register BOARD_ID --column-id TODO_COLUMN_ID --work-key UNIQUE_STABLE_KEY --title "Work" --description "Starting"`.
2. **Plan**: `python -m app.cli --json kanban log CARD_ID --kind plan --message "Specific steps"` (after obtaining CARD_ID).
3. **Progress**: rerun with the **same** key, DOING_COLUMN_ID and an honest progress description.
4. **Complete**: only after tests, rerun with the same key and DONE_COLUMN_ID, include verification details.
5. **Inspect**: `python -m app.cli --json kanban get CARD_ID` and compare returned IDs and status.

All `register` operations are implemented by FastAPI POST/PATCH + GET through `app/kanban/tracking.py`. Its UUID5 work key is deterministic per board+actor+key. This prevents duplicates for the same actor, not across different actors or work keys. HTTP permission errors and schema mismatches are never successful registration.

CLI common options (`--json`, `--actor-id`, `--url`) come **before** `kanban` subcommand. Prefer environment variables `TEAM_TODO_ACTOR_ID`, `TEAM_TODO_API_KEY` and `KANBAN_API_URL`; never print sensitive values. See project README for Windows PowerShell variations.


Activity endpoint: POST `/api/v1/cards/{card_id}/activities` with body `{"kind":"plan|progress|result|blocked", "message":"..."}`. Requires an editor/owner. The activity line is appended atomically to the existing description field with time, actor and kind; the existing 6-table schema is not modified. Use `kanban log` rather than repeatedly overwriting `--description` during work tracking. Verify all state transitions with GET.
