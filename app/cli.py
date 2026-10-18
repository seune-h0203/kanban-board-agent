"""Cross-platform Typer client covering all Assignment 7 Kanban endpoints."""
import json
import os
from typing import Annotated, Any
from uuid import UUID

import httpx
import typer

from app.kanban.cli import kanban
from app.kanban.shared_cli import shared

app = typer.Typer(help="Assignment 7 Kanban CLI (Windows, macOS, Linux)", no_args_is_help=True)
app.add_typer(kanban, name="kanban")
app.add_typer(shared, name="shared")


def _make_client(base_url: str) -> httpx.Client:
    """One HTTP client per CLI invocation."""
    return httpx.Client(base_url=base_url.rstrip("/"), timeout=15, follow_redirects=False)


def _request(
    ctx: typer.Context,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> httpx.Response | None:
    """Invoke an API endpoint with consistent headers and safe errors."""
    opts = ctx.obj
    headers = {"X-Actor-ID": str(opts["actor_id"])}
    if opts.get("api_key"):
        headers["X-API-Key"] = opts["api_key"]
    try:
        with _make_client(opts["base_url"]) as client:
            response = client.request(method, path, json=body, params=params, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get("detail", "Request failed")
        except (ValueError, AttributeError):
            detail = "Request failed"
        if opts["json"]:
            typer.echo(json.dumps({"error": {"status": error.response.status_code, "detail": detail}}, ensure_ascii=False), err=True)
        else:
            typer.echo(f"HTTP {error.response.status_code}: {detail}", err=True)
        raise typer.Exit(1) from error
    except httpx.RequestError as error:
        typer.echo("Unable to connect to the API. Verify --url and server state.", err=True)
        raise typer.Exit(1) from error
    return None if response.status_code == 204 else response


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Annotated[str, typer.Option("--url", help="FastAPI server URL.")] = os.getenv("KANBAN_API_URL", "http://127.0.0.1:8000"),
    actor_id: Annotated[UUID | None, typer.Option("--actor-id", help="Existing board member UUID.")] = None,
    api_key: Annotated[str | None, typer.Option("--api-key", help="Shared server secret. Prefer TEAM_TODO_API_KEY environment variable.")] = None,
    json_output: Annotated[bool, typer.Option("--json/--text", help="Machine-readable JSON or human-readable text.")] = False,
) -> None:
    """Set transport config once for all subcommands."""
    configured_actor = actor_id or os.getenv("TEAM_TODO_ACTOR_ID")
    try:
        actor = UUID(str(configured_actor)) if configured_actor else None
    except ValueError as error:
        raise typer.BadParameter("TEAM_TODO_ACTOR_ID must be a valid UUID.") from error
    ctx.obj = {
        "base_url": base_url,
        "actor_id": actor,
        "api_key": api_key or os.getenv("TEAM_TODO_API_KEY"),
        "json": json_output,
    }


@app.command("health")
def health(ctx: typer.Context) -> None:
    """Check server process readiness (not database health)."""
    from app.kanban.cli import show
    show(ctx, _request(ctx, "GET", "/health"))


if __name__ == "__main__":
    app()
