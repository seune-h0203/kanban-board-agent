"""Create a clearly labelled isolated demo; refuse PostgreSQL/shared seeding."""

import json
from uuid import NAMESPACE_URL, uuid5

import typer

from app.db.session import SessionLocal, engine
from app.kanban.models import Board, BoardMember, Column, User

DEMO = {
    name: str(uuid5(NAMESPACE_URL, f"assignment7-isolated/{name}"))
    for name in [
        "actor_id",
        "editor_id",
        "viewer_id",
        "board_id",
        "todo_id",
        "doing_id",
        "done_id",
    ]
}


def seed_demo() -> dict[str, str]:
    """Initialize demo profiles and workflow columns only in SQLite.

    Returns:
        Stable IDs for the explicitly isolated board.

    Raises:
        RuntimeError: The selected database is not a local SQLite database.

    """
    if engine.dialect.name != "sqlite":
        message = "Demo seeding is allowed only in an isolated SQLite database."
        raise RuntimeError(message)
    from uuid import UUID  # ruff: ignore[import-outside-top-level]

    ids = {name: UUID(value) for name, value in DEMO.items()}
    with SessionLocal() as db:
        if db.get(Board, ids["board_id"]) is not None:
            return DEMO
        for key, name in [
            ("actor_id", "Codex"),
            ("editor_id", "Team editor"),
            ("viewer_id", "Team viewer"),
        ]:
            db.add(User(id=ids[key], name=name, email=f"{key}@example.test"))
        db.flush()
        db.add(
            Board(
                id=ids["board_id"],
                owner_id=ids["actor_id"],
                name="Assignment 7 - ISOLATED DEMO",
                description=(
                    "Local verification only; shared Supabase integration pending."
                ),
            )
        )
        db.flush()
        db.add_all([
            BoardMember(board_id=ids["board_id"], user_id=ids[key], role=role)
            for key, role in [
                ("actor_id", "owner"),
                ("editor_id", "editor"),
                ("viewer_id", "viewer"),
            ]
        ])
        db.add_all([
            Column(id=ids[key], board_id=ids["board_id"], name=name, position=position)
            for key, name, position in [
                ("todo_id", "To Do", 1000),
                ("doing_id", "In Progress", 2000),
                ("done_id", "Done", 3000),
            ]
        ])
        db.commit()
    return DEMO


if __name__ == "__main__":
    typer.echo(json.dumps(seed_demo(), indent=2))
