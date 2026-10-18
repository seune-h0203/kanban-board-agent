"""Stable task registration using existing card APIs, without duplicate cards."""

from uuid import NAMESPACE_URL, UUID, uuid5

import httpx


def register_work(  # ruff: ignore[too-many-arguments]
    client: httpx.Client,
    *,
    board_id: UUID,
    actor_id: UUID,
    column_id: UUID,
    work_key: str,
    title: str,
    description: str | None = None,
) -> httpx.Response:
    """Create or update a deterministic task, then read the saved row back.

    Returns:
        The verified saved card response.

    Raises:
        ValueError: A stable ID resolves to a card on a different board or owner.

    HTTP failures propagate to the CLI; no automatic network retry occurs.

    """
    if not work_key.strip():
        raise ValueError("Use a nonempty, stable work key.")
    work_key = work_key.strip()
    card_id = uuid5(NAMESPACE_URL, f"kanban-work/{board_id}/{actor_id}/{work_key}")
    path = f"/api/v1/cards/{card_id}"
    existing = client.get(path)
    body = {"title": title, "column_id": str(column_id)}
    if description is not None:
        body["description"] = description
    if existing.status_code == httpx.codes.NOT_FOUND:
        response = client.post(
            f"/api/v1/boards/{board_id}/cards",
            json={
                **body,
                "id": str(card_id),
                "assignee_ids": [str(actor_id)],
            },
        )
        if response.status_code == httpx.codes.CONFLICT:
            # A concurrent caller may have committed this same deterministic ID.
            existing = client.get(path)
        else:
            response.raise_for_status()
    if existing.status_code != httpx.codes.NOT_FOUND:
        existing.raise_for_status()
        card = existing.json()
        if card["board_id"] != str(board_id) or card["created_by"] != str(actor_id):
            message = "The saved work ID belongs to a different board or creator."
            raise ValueError(message)
        client.patch(path, json=body).raise_for_status()
    saved = client.get(path)
    saved.raise_for_status()
    if (
        saved.json()["column_id"] != str(column_id)
        or saved.json()["title"] != title.strip()
        or saved.json()["board_id"] != str(board_id)
        or saved.json()["created_by"] != str(actor_id)
    ):
        message = "The saved task changed during verification. Read it before retrying."
        raise ValueError(message)
    return saved
