# Codex project instructions

- Preserve the original `kanban/` sources; implement changes in `app/`.
- Before changing code, review docs/PRD.md, TSD.md and TEST_CASE.md.
- Use the local `kanban-task-tracker` skill to register work, plan, progress, results and blockers when a configured board is available. Never claim remote DB registration without reading it back.
- After changes run `python -m pytest -q`, `python scripts/smoke_local.py`, and `ruff check .` if installed.
- Never auto-migrate real Supabase tables or expose secrets.
