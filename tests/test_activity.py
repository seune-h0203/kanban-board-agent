"""Activity history is persisted and cannot be edited by viewers."""
import json
from typer.testing import CliRunner
import app.cli as cli


def test_activity_log_persists_order_and_preserves_description(env, headers):
    client, ids, maker, _ = env
    created = client.post(f"/api/v1/boards/{ids['board_id']}/cards", headers=headers, json={
        "column_id": str(ids["todo_id"]), "title": "Codex task", "description": "scope: do not erase"
    })
    assert created.status_code == 201
    card_id = created.json()["id"]
    for kind, message in [("plan", "write tests"), ("progress", "changed tests/test_activity.py"), ("result", "pytest passed")]:
        response = client.post(f"/api/v1/cards/{card_id}/activities", headers=headers, json={"kind": kind, "message": message})
        assert response.status_code == 200, response.text
    saved = client.get(f"/api/v1/cards/{card_id}", headers=headers).json()
    description = saved["description"]
    assert description.startswith("scope: do not erase")
    assert description.index("write tests") < description.index("changed tests/test_activity.py") < description.index("pytest passed")
    assert description.count("[plan]") == 1
    with maker() as session:
        from app.kanban.models import Card
        from uuid import UUID
        assert "pytest passed" in session.get(Card, UUID(card_id)).description


def test_activity_rejects_viewer_unknown_kind_blank_message_and_full_log(env, headers):
    client, ids, maker, _ = env
    created = client.post(f"/api/v1/boards/{ids['board_id']}/cards", headers=headers, json={
        "column_id": str(ids["todo_id"]), "title": "task", "description": "x" * 4990
    })
    card_id = created.json()["id"]
    viewer_headers = {**headers, "X-Actor-ID": str(ids["viewer_id"])}
    endpoint = f"/api/v1/cards/{card_id}/activities"
    assert client.post(endpoint, headers=viewer_headers, json={"kind":"plan", "message":"read only"}).status_code == 403
    assert client.post(endpoint, headers=headers, json={"kind":"wrong", "message":"bad"}).status_code == 422
    assert client.post(endpoint, headers=headers, json={"kind":"plan", "message":"   "}).status_code == 422
    assert client.post(endpoint, headers=headers, json={"kind":"progress", "message":"a"}).status_code == 409
    assert client.get(f"/api/v1/cards/{card_id}", headers=headers).json()["description"] == "x" * 4990


def test_cli_activity_json_and_text(env, headers, monkeypatch):
    client, ids, _, _ = env
    monkeypatch.setattr(cli, "_make_client", lambda url: client)
    created = client.post(f"/api/v1/boards/{ids['board_id']}/cards", headers=headers, json={
        "column_id": str(ids["todo_id"]), "title": "CLI log task"
    })
    card_id = created.json()["id"]
    runner = CliRunner()
    common = ["--actor-id", str(ids["actor_id"]), "--api-key", "pytest-only-token"]
    saved = runner.invoke(cli.app, [*common, "--json", "kanban", "log", card_id, "--kind", "plan", "--message", "Write scenario"] )
    assert saved.exit_code == 0, (saved.output, saved.exception)
    assert "[plan]" in json.loads(saved.output)["description"]
    saved = runner.invoke(cli.app, [*common, "--text", "kanban", "log", card_id, "--kind", "result", "--message", "4 checks passed"] )
    assert saved.exit_code == 0 and "4 checks passed" in saved.output
