"""Read-only verification before attaching the existing shared board database."""

import json
import os

import typer
from sqlalchemy import create_engine, inspect, select

from app.kanban.models import Board, BoardMember, Card, CardAssignee, Column, User


def inspect_board_database(database_url: str) -> dict:
    """Inspect required columns and real board IDs without changing any rows.

    Returns:
        Compatibility findings and saved board/user/column identifiers.

    All checks use a read-only transaction. Connection failures propagate; the
    caller must report them as an unavailable integration rather than a save.

    """
    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 10}
        if database_url.startswith("postgresql")
        else {},
    )
    report: dict = {
        "mode": "read-only",
        "dialect": engine.dialect.name,
        "missing": [],
        "boards": [],
        "users": [],
        "columns": [],
        "tables": {},
    }
    try:
        with engine.connect() as connection:
            if engine.dialect.name == "postgresql":
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            else:
                connection.exec_driver_sql("PRAGMA query_only=ON")
            inspector = inspect(connection)
            for model in [User, Board, BoardMember, Column, Card, CardAssignee]:
                table = model.__table__
                if not inspector.has_table(table.name):
                    report["missing"].append(table.name)
                    continue
                saved_columns = inspector.get_columns(table.name)
                columns = {column["name"] for column in saved_columns}
                report["tables"][table.name] = {
                    "columns": [
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": column["nullable"],
                        }
                        for column in saved_columns
                    ],
                    "primary_key": inspector.get_pk_constraint(table.name),
                    "foreign_keys": inspector.get_foreign_keys(table.name),
                    "unique_constraints": inspector.get_unique_constraints(table.name),
                    "checks": inspector.get_check_constraints(table.name),
                }
                report["missing"].extend(
                    f"{table.name}.{column.name}"
                    for column in table.columns
                    if column.name not in columns
                )
            if not report["missing"]:
                for key, statement in [
                    ("boards", select(Board.id, Board.name, Board.owner_id)),
                    ("users", select(User.id, User.name)),
                    (
                        "columns",
                        select(
                            Column.id, Column.board_id, Column.name, Column.position
                        ),
                    ),
                ]:
                    report[key] = [
                        dict(value)
                        for value in connection.execute(statement).mappings()
                    ]
            connection.rollback()
    finally:
        engine.dispose()
    report["required_columns_present"] = not report["missing"]
    report["integration_ready"] = False
    report["note"] = (
        "Review types, constraints, RLS/DB role and selected IDs before writes. "
        "Column presence alone is not full compatibility."
    )
    return report


if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL")
    if not url:
        typer.echo("Set DATABASE_URL to the database you want to inspect.", err=True)
        raise SystemExit(2)
    typer.echo(json.dumps(inspect_board_database(url), default=str, indent=2))
