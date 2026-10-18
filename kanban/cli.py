"""Plain English commands for every kanban API operation."""

import json
from typing import Annotated
from uuid import UUID

import httpx
import typer

kanban = typer.Typer(
    help="Work with your shared board. First choose your user with --actor-id.",
    no_args_is_help=True,
)
Id = Annotated[UUID, typer.Argument(help="The saved ID shown by a list command.")]
ColumnOption = Annotated[
    UUID, typer.Option(help="The saved ID of the task's workflow column.")
]
Assignees = Annotated[
    list[UUID] | None,
    typer.Option(
        "--assignee-id", help="Assign a team member by ID. Repeat to add more people."
    ),
]


def show(ctx: typer.Context, response: httpx.Response | None) -> None:
    """Display JSON for tools or readable labels for people."""
    if response is None:
        if not ctx.obj["json"]:
            typer.echo("Task deleted.")
        return
    data = response.json()
    if ctx.obj["json"]:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    items = data.get("items", [data])
    if not items:
        typer.echo("No results found.")
    for item in items:
        for key, value in item.items():
            label = key.replace("_", " ").capitalize()
            shown = value if value is not None else "-"
            typer.echo(f"{label}: {shown}")
        typer.echo()


def call(
    ctx: typer.Context,
    method: str,
    path: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
) -> None:
    """Use the same HTTP/error handling as the existing Todo commands.

    Raises:
        typer.BadParameter: Required options are missing or conflicting.

    """
    from app.cli import _request  # ruff: ignore[import-outside-top-level]

    if not ctx.obj.get("actor_id"):
        message = "Choose your team user with --actor-id or TEAM_TODO_ACTOR_ID."
        raise typer.BadParameter(message)
    show(ctx, _request(ctx, method, f"/api/v1{path}", params=params, body=body))


@kanban.command(help="Show team user IDs and names. Example: ttodo kanban users")
def users(ctx: typer.Context) -> None:
    """Show team profiles."""
    call(ctx, "GET", "/users")


@kanban.command(help="Show boards you belong to. Example: ttodo kanban boards")
def boards(ctx: typer.Context) -> None:
    """Show shared boards."""
    call(ctx, "GET", "/boards")


@kanban.command(help="Show one board's details. Example: ttodo kanban board BOARD_ID")
def board(ctx: typer.Context, board_id: Id) -> None:
    """Show a board."""
    call(ctx, "GET", f"/boards/{board_id}")


@kanban.command(
    help=(
        "Show who belongs to a board and their role. Example: "
        "ttodo kanban members BOARD_ID"
    )
)
def members(ctx: typer.Context, board_id: Id) -> None:
    """Show team membership."""
    call(ctx, "GET", f"/boards/{board_id}/members")


@kanban.command(
    help=(
        "Show the board's workflow steps in order. Example: "
        "ttodo kanban columns BOARD_ID"
    )
)
def columns(ctx: typer.Context, board_id: Id) -> None:
    """Find the column IDs to use when creating or moving a task."""
    call(ctx, "GET", f"/boards/{board_id}/columns")


@kanban.command(
    name="list", help="Show saved tasks on a board. Example: ttodo kanban list BOARD_ID"
)
def list_cards(
    ctx: typer.Context,
    board_id: Id,
    column_id: Annotated[
        UUID | None, typer.Option(help="Show only tasks in this workflow step.")
    ] = None,
    assignee_id: Annotated[
        UUID | None, typer.Option(help="Show tasks assigned to this person.")
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            min=1, max=100, help="The most tasks to show (1-100; default 50)."
        ),
    ] = 50,
    offset: Annotated[
        int, typer.Option(min=0, help="How many tasks to skip (default 0).")
    ] = 0,
) -> None:
    """Show tasks in workflow order, with optional person and step filters."""
    params: dict[str, str | int] = {"limit": limit, "offset": offset}
    if column_id is not None:
        params["column_id"] = str(column_id)
    if assignee_id is not None:
        params["assignee_id"] = str(assignee_id)
    call(ctx, "GET", f"/boards/{board_id}/cards", params=params)


@kanban.command(
    name="create",
    help=(
        "Save a team task. Example: ttodo kanban create BOARD_ID "
        '--column-id COLUMN_ID --title "Prepare presentation"'
    ),
)
def create(
    ctx: typer.Context,
    board_id: Id,
    column_id: ColumnOption,
    title: Annotated[
        str, typer.Option(help="A short task name (required, 1-200 characters).")
    ],
    description: Annotated[
        str | None,
        typer.Option(help="More details about the work (up to 5000 characters)."),
    ] = None,
    due_date: Annotated[
        str | None,
        typer.Option(
            help=(
                "When the task is due. Include the timezone: 2026-10-20T09:00:00+09:00."
            )
        ),
    ] = None,
    assignee_id: Assignees = None,
    card_id: Annotated[
        UUID | None,
        typer.Option(
            help=(
                "An optional stable task ID for safe retries. Read this "
                "ID before retrying."
            )
        ),
    ] = None,
) -> None:
    """Save one card and its assigned people on the chosen board."""
    body = {
        "column_id": str(column_id),
        "title": title,
        "description": description,
        "due_date": due_date,
        "assignee_ids": [str(value) for value in assignee_id or []],
    }
    if card_id is not None:
        body["id"] = str(card_id)
    call(ctx, "POST", f"/boards/{board_id}/cards", body=body)


@kanban.command(
    help="Show a task and its assigned people. Example: ttodo kanban get CARD_ID"
)
def get(ctx: typer.Context, card_id: Id) -> None:
    """Read one saved task."""
    call(ctx, "GET", f"/cards/{card_id}")


@kanban.command(
    help=(
        "Change only the details you provide. Use --column-id to "
        "move a task to another step. Example: ttodo kanban "
        "update CARD_ID --column-id DONE_COLUMN_ID"
    )
)
def update(
    ctx: typer.Context,
    card_id: Id,
    title: Annotated[
        str | None, typer.Option(help="A new short name for the task.")
    ] = None,
    column_id: Annotated[
        UUID | None, typer.Option(help="Move the task to this step on the same board.")
    ] = None,
    description: Annotated[
        str | None, typer.Option(help="Replace the task's description.")
    ] = None,
    due_date: Annotated[
        str | None,
        typer.Option(
            help="Replace the due time, including timezone (for example +09:00)."
        ),
    ] = None,
    assignee_id: Assignees = None,
    clear_description: Annotated[
        bool, typer.Option(help="Remove the description.")
    ] = False,
    clear_due_date: Annotated[bool, typer.Option(help="Remove the due time.")] = False,
    clear_assignees: Annotated[
        bool, typer.Option(help="Remove all assigned people.")
    ] = False,
) -> None:
    """Preserve omitted details and explicitly clear optional fields.

    Raises:
        typer.BadParameter: Required options are missing or conflicting.

    """
    for clear, value, label in [
        (clear_description, description, "description"),
        (clear_due_date, due_date, "due-date"),
        (clear_assignees, assignee_id, "assignee-id"),
    ]:
        if clear and value is not None:
            message = f"Choose either the {label} value or its clear option."
            raise typer.BadParameter(message)
    body = {
        key: value
        for key, value in {
            "title": title,
            "column_id": str(column_id) if column_id else None,
            "description": description,
            "due_date": due_date,
            "assignee_ids": [str(value) for value in assignee_id]
            if assignee_id is not None
            else None,
        }.items()
        if value is not None
    }
    clear_fields = [
        (clear_description, "description", None),
        (clear_due_date, "due_date", None),
        (clear_assignees, "assignee_ids", []),
    ]
    body.update({key: value for clear, key, value in clear_fields if clear})
    if not body:
        message = "Choose at least one task detail to change."
        raise typer.BadParameter(message)
    call(ctx, "PATCH", f"/cards/{card_id}", body=body)


@kanban.command(
    help=(
        "Delete a task permanently. This cannot be undone. "
        "Example: ttodo kanban delete CARD_ID"
    )
)
def delete(ctx: typer.Context, card_id: Id) -> None:
    """Remove the card and its assignments."""
    call(ctx, "DELETE", f"/cards/{card_id}")


@kanban.command(
    help=(
        "Save or update Codex work without creating duplicate tasks. "
        "Keep the same work key when resuming. Example: ttodo kanban register "
        "BOARD_ID --column-id COLUMN_ID --work-key backend --title Build"
    )
)
def register(
    ctx: typer.Context,
    board_id: Id,
    column_id: ColumnOption,
    work_key: Annotated[
        str,
        typer.Option(help="A stable name for this work item. Reuse it when resuming."),
    ],
    title: Annotated[str, typer.Option(help="A short name for the current work.")],
    description: Annotated[
        str | None, typer.Option(help="Progress, results or remaining blockers.")
    ] = None,
) -> None:
    """Register ongoing work and read the saved result before reporting success.

    Raises:
        typer.BadParameter: Required options are missing or conflicting.
        typer.Exit: The server cannot save and verify the work item.

    """
    from app.cli import _make_client  # ruff: ignore[import-outside-top-level]
    from app.kanban.tracking import register_work  # ruff: ignore[import-outside-top-level]

    actor = ctx.obj.get("actor_id")
    if not actor:
        message = "Choose your team user with --actor-id or TEAM_TODO_ACTOR_ID."
        raise typer.BadParameter(message)
    try:
        with _make_client(ctx.obj["base_url"]) as client:
            client.headers["X-Actor-ID"] = str(actor)
            if ctx.obj.get("api_key"):
                client.headers["X-API-Key"] = ctx.obj["api_key"]
            result = register_work(
                client,
                board_id=board_id,
                actor_id=actor,
                column_id=column_id,
                work_key=work_key,
                title=title,
                description=description,
            )
    except (httpx.HTTPError, ValueError) as error:
        typer.echo(
            f"Work registration failed: {error}. Read the saved task before retrying.",
            err=True,
        )
        raise typer.Exit(1) from error
    show(ctx, result)
