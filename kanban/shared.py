"""Optional single-card tracking through Supabase's existing Data API.

This companion does not replace the transactional SQLAlchemy backend. It never
changes schema or RLS and does not mutate multi-table assignments.
"""

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.kanban.schemas import CardCreate


class SharedBoard:
    """Use a caller-configured Data API client and an existing team actor."""

    def __init__(self, client: httpx.Client, *, actor_id: str) -> None:
        """Keep the client lifecycle and credentials with the caller."""
        self.client = client
        self.actor_id = str(UUID(actor_id))

    def rows(self, table: str, **filters: str) -> list[dict[str, Any]]:
        """Read existing rows using PostgREST filters.

        Returns:
            The visible rows. Empty results never prove that RLS allowed access.

        """
        response = self.client.get(table, params=filters)
        response.raise_for_status()
        return response.json()

    def membership(self, board_id: str, *, write: bool = False) -> None:
        """Require visible board membership before reads or writes.

        Raises:
            ValueError: Membership is hidden, absent, or read-only.

        """
        members = self.rows(
            "board_members", board_id=f"eq.{board_id}", user_id=f"eq.{self.actor_id}"
        )
        if not members or (write and members[0]["role"] not in {"owner", "editor"}):
            message = "Board membership is unavailable or does not allow this action."
            raise ValueError(message)

    def column(self, column_id: str, board_id: str | None = None) -> str:
        """Resolve a visible workflow column and enforce the chosen board.

        Returns:
            The actual board ID.

        Raises:
            ValueError: The column is hidden, missing, or belongs to another board.

        """
        columns = self.rows("columns", id=f"eq.{column_id}")
        if not columns or (board_id and columns[0]["board_id"] != board_id):
            message = "Choose a visible column on the selected board."
            raise ValueError(message)
        return columns[0]["board_id"]

    def get(self, card_id: str, *, board_id: str | None = None) -> dict[str, Any]:
        """Read a persisted card after checking its actual board membership.

        Returns:
            The saved card and resolved board ID.

        Raises:
            ValueError: A visible saved card cannot be verified.

        """
        cards = self.rows("cards", id=f"eq.{UUID(card_id)}")
        if not cards:
            message = "Saved card is not visible. Check its ID, credentials and RLS."
            raise ValueError(message)
        card = cards[0]
        actual_board = self.column(card["column_id"], board_id)
        self.membership(actual_board)
        return {**card, "board_id": actual_board}

    def register(
        self,
        *,
        board_id: str,
        column_id: str,
        work_key: str,
        title: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Register one stable work card and verify it with a separate read.

        Returns:
            The independently read saved card.

        Raises:
            ValueError: Inputs, membership, ownership, or read-back fail verification.

        Each mutation is one Data API transaction. Position conflicts and ambiguous
        network failures stop the operation; reuse the work-key on a manual retry.
        Existing assignment rows are untouched.

        """
        board_id = str(UUID(board_id))
        column_id = str(UUID(column_id))
        body = CardCreate(
            title=title, column_id=UUID(column_id), description=description
        ).model_dump(mode="json", exclude={"id", "assignee_ids", "due_date"})
        if not work_key.strip():
            message = "Choose a stable, nonempty work key."
            raise ValueError(message)
        self.membership(board_id, write=True)
        self.column(column_id, board_id)
        card_id = str(
            uuid5(NAMESPACE_URL, f"kanban-work/{board_id}/{self.actor_id}/{work_key}")
        )
        existing = self.rows("cards", id=f"eq.{card_id}")
        if existing:
            card = self.get(card_id, board_id=board_id)
            if card["created_by"] != self.actor_id:
                message = "The saved work card belongs to a different creator."
                raise ValueError(message)
            if description is None:
                body.pop("description")
            if card["column_id"] != column_id:
                body["position"] = self.next_position(column_id)
            response = self.client.patch(
                "cards", params={"id": f"eq.{card_id}"}, json=body
            )
        else:
            response = self.client.post(
                "cards",
                json={
                    **body,
                    "id": card_id,
                    "created_by": self.actor_id,
                    "position": self.next_position(column_id),
                },
            )
        response.raise_for_status()
        saved = self.get(card_id, board_id=board_id)
        matches = [saved["title"] == body["title"], saved["column_id"] == column_id]
        if description is not None:
            matches.append(saved["description"] == description)
        if not all(matches):
            message = "Saved work changed during verification. Read it before retrying."
            raise ValueError(message)
        return saved

    def next_position(self, column_id: str) -> int:
        """Append with the existing board spacing convention.

        Returns:
            The next available position observed at read time.

        """
        rows = self.rows(
            "cards",
            column_id=f"eq.{column_id}",
            select="position",
            order="position.desc",
            limit="1",
        )
        return (rows[0]["position"] if rows else 0) + 1000
