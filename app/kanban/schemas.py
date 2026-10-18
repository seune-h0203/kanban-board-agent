"""Validated card inputs; patch preserves omitted fields."""

from datetime import UTC, datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

MAX_TITLE = 200
MAX_DESCRIPTION = 5000


class CardFields(BaseModel):
    """Card fields supported by the existing board schema."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", check_fields=False)
    @classmethod
    def title_valid(cls, value: str | None) -> str:
        """Require a nonempty, bounded title when explicitly supplied.

        Returns:
            The trimmed task title.

        Raises:
            ValueError: A supplied field does not satisfy the documented input rules.

        """
        if value is None or not 1 <= len(value.strip()) <= MAX_TITLE:
            message = "Use a title between 1 and 200 characters."
            raise ValueError(message)
        return value.strip()

    @field_validator("column_id", "assignee_ids", check_fields=False)
    @classmethod
    def not_null(cls, value: UUID | list[UUID] | None) -> UUID | list[UUID]:
        """Reject explicit null for workflow and assignments.

        Returns:
            The supplied non-null value.

        Raises:
            ValueError: A supplied field does not satisfy the documented input rules.

        """
        if value is None:
            message = "This field cannot be null."
            raise ValueError(message)
        return value

    @field_validator("description", check_fields=False)
    @classmethod
    def description_valid(cls, value: str | None) -> str | None:
        """Bound free text while allowing clearing.

        Returns:
            The description or an explicit clearing value.

        Raises:
            ValueError: A supplied field does not satisfy the documented input rules.

        """
        if value is not None and len(value) > MAX_DESCRIPTION:
            message = "Use at most 5000 characters."
            raise ValueError(message)
        return value

    @field_validator("due_date", check_fields=False)
    @classmethod
    def due_valid(cls, value: datetime | None) -> datetime | None:
        """Require an explicit timezone, matching timestamptz.

        Returns:
            The UTC timestamp or an explicit clearing value.

        Raises:
            ValueError: A supplied field does not satisfy the documented input rules.

        """
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                message = "Include a timezone, for example +09:00 or Z."
                raise ValueError(message)
            return value.astimezone(UTC)
        return None


class CardCreate(CardFields):
    """New card with optional client-selected UUID for safe retries."""

    title: str
    column_id: UUID
    id: UUID | None = None
    description: str | None = None
    due_date: datetime | None = None
    assignee_ids: list[UUID] | None = None


class CardPatch(CardFields):
    """Only explicit fields change; empty updates are rejected."""

    title: str | None = None
    column_id: UUID | None = None
    description: str | None = None
    due_date: datetime | None = None
    assignee_ids: list[UUID] | None = None

    @model_validator(mode="after")
    def has_changes(self) -> "CardPatch":
        """Reject updates with no fields.

        Returns:
            The validated partial update.

        Raises:
            ValueError: A supplied field does not satisfy the documented input rules.

        """
        if not self.model_fields_set:
            message = "Choose at least one detail to change."
            raise ValueError(message)
        return self


class CardActivity(BaseModel):
    """One append-only human/Codex activity entry using the existing description field."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal["plan", "progress", "result", "blocked"]
    message: str

    @field_validator("message")
    @classmethod
    def valid_message(cls, value: str) -> str:
        """Reject empty or oversized log entries and normalize line breaks."""
        normalized = " ".join(value.split())
        if not 1 <= len(normalized) <= 700:
            raise ValueError("An activity message must contain 1-700 characters.")
        return normalized
