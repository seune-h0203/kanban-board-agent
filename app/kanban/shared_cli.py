"""Explicit Data API companion for existing shared-board task tracking."""

import os
from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

import httpx
import typer

from app.kanban.cli import show
from app.kanban.shared import SharedBoard

shared = typer.Typer(
    help=(
        "Track work through the existing Supabase Data API. "
        "Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY first."
    ),
    no_args_is_help=True,
)
Id = Annotated[UUID, typer.Argument(help="An existing shared board or card ID.")]


def execute(
    ctx: typer.Context, action: Callable[[SharedBoard], dict[str, Any]]
) -> None:
    """Run one authorized operation without printing access credentials.

    Raises:
        typer.BadParameter: The Data API settings or actor are missing.
        typer.Exit: Saving or verifying the shared record failed.

    """
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    actor = ctx.obj.get("actor_id")
    token = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if not url.startswith("https://") or not key or not token or not actor:
        message = (
            "Set SUPABASE_URL (HTTPS), SUPABASE_PUBLISHABLE_KEY, "
            "SUPABASE_ACCESS_TOKEN (user JWT) and --actor-id."
        )
        raise typer.BadParameter(message)
    try:
        with httpx.Client(
            base_url=f"{url}/rest/v1/",
            headers={"apikey": key, "Authorization": f"Bearer {token}"},
            timeout=15,
        ) as client:
            result = action(SharedBoard(client, actor_id=str(actor)))
    except (httpx.HTTPError, ValueError) as error:
        status = (
            error.response.status_code
            if isinstance(error, httpx.HTTPStatusError)
            else None
        )
        reason = f"HTTP {status}" if status else "Connection or verification failure"
        typer.echo(
            f"Shared board action failed: {reason}. "
            "Check access and read the work card before retrying.",
            err=True,
        )
        raise typer.Exit(1) from error
    show(ctx, httpx.Response(200, json=result))


@shared.command(help="Read a saved shared task. Example: kanban7 shared get CARD_ID")
def get(ctx: typer.Context, card_id: Id) -> None:
    """Read the saved card and check its board membership."""
    execute(ctx, lambda service: service.get(str(card_id)))


@shared.command(
    help=(
        "Save or resume one Codex work card. Reuse the same --work-key; "
        "this leaves assigned people unchanged."
    )
)
def register(  # ruff: ignore[too-many-arguments,too-many-positional-arguments]
    ctx: typer.Context,
    board_id: Id,
    column_id: Annotated[
        UUID, typer.Option(help="An existing workflow column on this board.")
    ],
    work_key: Annotated[
        str, typer.Option(help="A stable work name. Reuse it on every update.")
    ],
    title: Annotated[
        str, typer.Option(help="A short name for the work (1-200 characters).")
    ],
    description: Annotated[
        str | None, typer.Option(help="Progress or remaining blockers.")
    ] = None,
) -> None:
    """Register work without recreating the board or altering its schema."""
    execute(
        ctx,
        lambda service: service.register(
            board_id=str(board_id),
            column_id=str(column_id),
            work_key=work_key,
            title=title,
            description=description,
        ),
    )
