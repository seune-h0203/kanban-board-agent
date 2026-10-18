"""Board discovery and transactional card operations on Assignment 5 tables."""

import os
import secrets
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_db, serialize_sqlite_write
from app.kanban.models import Board, BoardMember, Card, CardAssignee, Column, User
from app.kanban.schemas import CardActivity, CardCreate, CardPatch, MAX_DESCRIPTION


def access(
    x_actor_id: Annotated[UUID, Header()],
    x_api_key: Annotated[str | None, Header()] = None,
) -> UUID:
    """Identify a trusted caller and verify the configured shared service key.

    Returns:
        The validated actor UUID.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    key = os.environ.get("TEAM_TODO_API_KEY")
    if not key:
        if os.environ.get("KANBAN_ALLOW_INSECURE_DEMO") != "1":
            raise HTTPException(503, "Server requires TEAM_TODO_API_KEY configuration.")
    elif not secrets.compare_digest(x_api_key or "", key):
        raise HTTPException(401, "A valid team access key is required.")
    return x_actor_id


router = APIRouter(prefix="/api/v1", tags=["Kanban"])
Database = Annotated[Session, Depends(get_db)]
Actor = Annotated[UUID, Depends(access)]


def require_board(
    db: Session, board_id: UUID, actor: UUID, *, write: bool = False
) -> Board:
    """Check membership and serialize PostgreSQL writes within one board.

    Returns:
        The visible board, locked when writing.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    statement = select(Board).where(Board.id == board_id)
    if write:
        statement = statement.with_for_update()
    board = db.scalar(statement)
    if board is None:
        raise HTTPException(404, "Board not found.")
    member = db.get(BoardMember, (board_id, actor))
    if member is None or (write and member.role not in {"owner", "editor"}):
        raise HTTPException(403, "You do not have permission for this board action.")
    return board


def require_column(db: Session, column_id: UUID, board_id: UUID) -> Column:
    """Reject cross-board references instead of moving someone else's task.

    Returns:
        The column belonging to the specified board.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    column = db.get(Column, column_id)
    if column is None or column.board_id != board_id:
        raise HTTPException(422, "Choose a column on this board.")
    return column


def card_board(db: Session, card_id: UUID) -> tuple[Card, UUID]:
    """Resolve the actual board rather than trusting a caller-supplied board.

    Returns:
        The stored card and its actual board UUID.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(404, "Card not found.")
    column = db.get(Column, card.column_id)
    if column is None:
        raise HTTPException(409, "The card has no valid column.")
    return card, column.board_id


def row(entity: Base) -> dict[str, Any]:
    """Return stored columns with UTC restored for SQLite timestamps.

    Returns:
        A dictionary of stored fields with UTC timestamps.

    """
    data = {
        column.name: getattr(entity, column.name) for column in entity.__table__.columns
    }
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = (
                value.replace(tzinfo=UTC)
                if value.tzinfo is None
                else value.astimezone(UTC)
            )
    return data


def card_result(db: Session, card: Card, board_id: UUID) -> dict[str, Any]:
    """Include board context and normalized multiple assignee IDs.

    Returns:
        The card, its board ID and assigned user IDs.

    """
    data = row(card)
    data["board_id"] = board_id
    data["assignee_ids"] = list(
        db.scalars(
            select(CardAssignee.user_id)
            .where(CardAssignee.card_id == card.id)
            .order_by(CardAssignee.user_id)
        )
    )
    return data


def assignments(db: Session, card: Card, board_id: UUID, ids: list[UUID]) -> None:
    """Validate every member before replacing the assignment junction rows.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    unique_ids = set(ids)
    members = set(
        db.scalars(
            select(BoardMember.user_id).where(
                BoardMember.board_id == board_id, BoardMember.user_id.in_(unique_ids)
            )
        )
    )
    if unique_ids != members:
        raise HTTPException(422, "Every assigned person must belong to this board.")
    db.execute(delete(CardAssignee).where(CardAssignee.card_id == card.id))
    db.add_all([
        CardAssignee(card_id=card.id, user_id=user_id) for user_id in unique_ids
    ])


def next_position(db: Session, column_id: UUID) -> int:
    """Append using the spacing convention in the original board spec.

    Returns:
        The next spaced integer position in the target column.

    """
    value = db.scalar(
        select(func.max(Card.position)).where(Card.column_id == column_id)
    )
    return (value or 0) + 1000


def commit(db: Session, *, flush_only: bool = False) -> None:
    """Rollback constraint conflicts without exposing SQL or credentials.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    try:
        if flush_only:
            db.flush()
        else:
            db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            409, "The change conflicts with an existing record."
        ) from error


@router.get("/users")
def users(db: Database, actor: Actor) -> dict[str, Any]:
    """Discover profiles in the trusted local service.

    Returns:
        The existing user profiles.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    if db.get(User, actor) is None:
        raise HTTPException(403, "Choose an existing team user.")
    return {
        "items": [row(user) for user in db.scalars(select(User).order_by(User.name))]
    }


@router.get("/boards")
def boards(db: Database, actor: Actor) -> dict[str, Any]:
    """List only boards the caller belongs to.

    Returns:
        The boards visible to this actor.

    """
    statement = select(Board).join(BoardMember).where(BoardMember.user_id == actor)
    return {
        "items": [row(board) for board in db.scalars(statement.order_by(Board.name))]
    }


@router.get("/boards/{board_id}")
def get_board(board_id: UUID, db: Database, actor: Actor) -> dict[str, Any]:
    """Show board details.

    Returns:
        The requested board details.

    """
    return row(require_board(db, board_id, actor))


@router.get("/boards/{board_id}/members")
def members(board_id: UUID, db: Database, actor: Actor) -> dict[str, Any]:
    """Show existing membership and roles.

    Returns:
        The saved memberships and roles.

    """
    require_board(db, board_id, actor)
    return {
        "items": [
            row(member)
            for member in db.scalars(
                select(BoardMember)
                .where(BoardMember.board_id == board_id)
                .order_by(BoardMember.user_id)
            )
        ]
    }


@router.get("/boards/{board_id}/columns")
def columns(board_id: UUID, db: Database, actor: Actor) -> dict[str, Any]:
    """Show workflow columns in their saved order.

    Returns:
        The workflow columns sorted by position.

    """
    require_board(db, board_id, actor)
    return {
        "items": [
            row(column)
            for column in db.scalars(
                select(Column)
                .where(Column.board_id == board_id)
                .order_by(Column.position)
            )
        ]
    }


@router.get("/boards/{board_id}/cards")
def cards(
    board_id: UUID,
    db: Database,
    actor: Actor,
    column_id: UUID | None = None,
    assignee_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    """List board tasks with filters and bounded pages.

    Returns:
        The filtered and bounded page of saved cards.

    """
    require_board(db, board_id, actor)
    statement = select(Card).join(Column).where(Column.board_id == board_id)
    if column_id is not None:
        require_column(db, column_id, board_id)
        statement = statement.where(Card.column_id == column_id)
    if assignee_id is not None:
        statement = statement.join(CardAssignee).where(
            CardAssignee.user_id == assignee_id
        )
    statement = (
        statement
        .order_by(Column.position, Card.position, Card.id)
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [card_result(db, card, board_id) for card in db.scalars(statement)],
        "limit": limit,
        "offset": offset,
    }


@router.post("/boards/{board_id}/cards", status_code=201)
def create_card(
    board_id: UUID, body: CardCreate, db: Database, actor: Actor
) -> dict[str, Any]:
    """Save a task, creator and assignments in one transaction.

    Returns:
        The committed card and its assignments.

    Raises:
        HTTPException: The resource, input or board permission check fails.

    """
    with serialize_sqlite_write(db):
        require_board(db, board_id, actor, write=True)
        require_column(db, body.column_id, board_id)
        card_id = body.id or uuid4()
        if db.get(Card, card_id) is not None:
            raise HTTPException(
                409, "This card ID already exists. Read it before retrying."
            )
        card = Card(
            id=card_id,
            column_id=body.column_id,
            title=body.title,
            description=body.description,
            due_date=body.due_date,
            created_by=actor,
            position=next_position(db, body.column_id),
        )
        db.add(card)
        commit(db, flush_only=True)
        assignments(db, card, board_id, body.assignee_ids or [])
        commit(db)
        return card_result(db, card, board_id)


@router.get("/cards/{card_id}")
def get_card(card_id: UUID, db: Database, actor: Actor) -> dict[str, Any]:
    """Read a saved task visible to the caller.

    Returns:
        The visible saved card.

    """
    card, board_id = card_board(db, card_id)
    require_board(db, board_id, actor)
    return card_result(db, card, board_id)


@router.patch("/cards/{card_id}")
def update_card(
    card_id: UUID, body: CardPatch, db: Database, actor: Actor
) -> dict[str, Any]:
    """Change supplied fields and append to the chosen workflow column.

    Returns:
        The updated card after the transaction commits.

    Raises:
        HTTPException: The card was removed before the write lock was acquired.

    """
    with serialize_sqlite_write(db):
        card, board_id = card_board(db, card_id)
        require_board(db, board_id, actor, write=True)
        card = db.get(Card, card_id, populate_existing=True)
        if card is None:
            raise HTTPException(404, "Card not found.")
        changes = body.model_dump(exclude_unset=True)
        if body.column_id is not None:
            require_column(db, body.column_id, board_id)
            if body.column_id != card.column_id:
                card.position = next_position(db, body.column_id)
        for key, value in changes.items():
            if key != "assignee_ids":
                setattr(card, key, value)
        if body.assignee_ids is not None:
            assignments(db, card, board_id, body.assignee_ids)
        card.updated_at = datetime.now(UTC)
        commit(db)
        return card_result(db, card, board_id)


@router.post("/cards/{card_id}/activities")
def add_card_activity(
    card_id: UUID, body: CardActivity, db: Database, actor: Actor
) -> dict[str, Any]:
    """Append a dated, attributable work note without adding a new DB table.

    The existing description remains intact; the complete history is bounded
    to the card's 5,000-character field contract. The board's write lock
    serializes updates on PostgreSQL, and SQLite uses BEGIN IMMEDIATE.
    """
    with serialize_sqlite_write(db):
        card, board_id = card_board(db, card_id)
        require_board(db, board_id, actor, write=True)
        card = db.get(Card, card_id, populate_existing=True)
        if card is None:
            raise HTTPException(404, "Card not found.")
        timestamp = datetime.now(UTC).isoformat(timespec="seconds")
        entry = f"[{timestamp}][{body.kind}][{actor}] {body.message}"
        current = card.description or ""
        proposed = f"{current}\n{entry}" if current else entry
        if len(proposed) > MAX_DESCRIPTION:
            raise HTTPException(409, "Activity history is full (5000 characters). Archive it before adding more.")
        card.description = proposed
        card.updated_at = datetime.now(UTC)
        commit(db)
        return card_result(db, card, board_id)


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: UUID, db: Database, actor: Actor) -> Response:
    """Delete a task and its assignment rows without changing the team.

    Returns:
        An empty success response.

    Raises:
        HTTPException: The card was removed before the write lock was acquired.

    """
    with serialize_sqlite_write(db):
        card, board_id = card_board(db, card_id)
        require_board(db, board_id, actor, write=True)
        card = db.get(Card, card_id, populate_existing=True)
        if card is None:
            raise HTTPException(404, "Card not found.")
        db.execute(delete(CardAssignee).where(CardAssignee.card_id == card_id))
        db.delete(card)
        commit(db)
    return Response(status_code=204)
