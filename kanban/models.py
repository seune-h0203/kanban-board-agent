"""The six Assignment 5 tables, without changing the legacy Todo model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def now() -> datetime:
    """Return the current UTC time.

    Returns:
        The current UTC timestamp.

    """
    return datetime.now(UTC)


class Timestamps:
    """Timestamps shared by the four entities."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class User(Timestamps, Base):
    """Existing team profile; authentication is handled outside this table."""

    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)


class Board(Timestamps, Base):
    """A shared board whose owner also has a membership."""

    __tablename__ = "boards"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)


class BoardMember(Base):
    """Board membership with the original composite primary key."""

    __tablename__ = "board_members"
    __table_args__ = (CheckConstraint("role IN ('owner','editor','viewer')"),)
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(Text, default="editor")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Column(Timestamps, Base):
    """A workflow state belonging to one board."""

    __tablename__ = "columns"
    __table_args__ = (
        UniqueConstraint(
            "board_id", "position", name="uq_columns_position_sqlite"
        ).ddl_if(dialect="sqlite"),
        UniqueConstraint(
            "board_id",
            "position",
            name="uq_columns_position_pg",
            deferrable=True,
            initially="DEFERRED",
        ).ddl_if(dialect="postgresql"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    position: Mapped[int]


class Card(Timestamps, Base):
    """A real team task stored in the original cards table."""

    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint(
            "column_id", "position", name="uq_cards_position_sqlite"
        ).ddl_if(dialect="sqlite"),
        UniqueConstraint(
            "column_id",
            "position",
            name="uq_cards_position_pg",
            deferrable=True,
            initially="DEFERRED",
        ).ddl_if(dialect="postgresql"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    column_id: Mapped[UUID] = mapped_column(
        ForeignKey("columns.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int]
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )


class CardAssignee(Base):
    """Multiple team members assigned to a card."""

    __tablename__ = "card_assignees"
    card_id: Mapped[UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
